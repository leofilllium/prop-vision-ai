"""
AI-powered search service using OpenAI GPT-4o-mini for query parsing.

Converts natural language property queries into structured PostGIS filters
using OpenAI's structured output API with the Uzbek RAG glossary.
"""

import json
import logging
import re
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists, and_
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.property import Property
from app.models.comfort import ComfortScore
from app.models.poi import POI
from app.models.analytics import SearchQuery
from app.schemas.search import ParsedFilters
from app.services.rag_context import load_rag_context

logger = logging.getLogger("propvision.services.ai_search")
settings = get_settings()

PROXIMITY_TO_COMFORT_SORT_MAP = {
    "metro_station": "transport",
    "bus_stop": "transport",
    "park": "green_space",
    "school": "education",
    "supermarket": "shopping",
    "hospital": "healthcare",
}

COMFORT_QUERY_KEYWORDS = {
    "transport": [
        "transport",
        "metro",
        "bus",
        "метро",
        "транспорт",
        "автобус",
        "остановка",
        "bekat",
        "metro yaqinida",
        "transportga yaqin",
        "станция",
        "way",
        "путь",
    ],
    "shopping": [
        "shopping",
        "shop",
        "supermarket",
        "market",
        "магазин",
        "супермаркет",
        "рынок",
        "do'kon",
        "bozor",
        "savdo",
        "маркет",
        "базар",
    ],
    "education": [
        "education",
        "school",
        "schools",
        "university",
        "maktab",
        "школ",
        "университет",
        "ta'lim",
        "bog'cha",
        "детский сад",
        "колледж",
        "институт",
    ],
    "green_space": [
        "park",
        "parks",
        "green",
        "nature",
        "парк",
        "парков",
        "зел",
        "bog'",
        "yashil",
        "сад",
        "сквер",
        "дерев",
        "nature",
    ],
    "safety": [
        "safe",
        "safest",
        "safety",
        "secure",
        "безопас",
        "безопасн",
        "xavfsiz",
        "спокойн",
        "тихи",
        "охрана",
        "безопасно",
    ],
    "healthcare": [
        "health",
        "healthcare",
        "hospital",
        "clinic",
        "medical",
        "больниц",
        "клиник",
        "медицин",
        "shifoxona",
        "klinika",
        "аптека",
        "dorixona",
        "врач",
    ],
    "entertainment": [
        "entertainment",
        "fun",
        "cinema",
        "theatre",
        "sports",
        "развлеч",
        "кино",
        "театр",
        "sport",
        "ko'ngilochar",
        "ресторан",
        "кафе",
        "гулять",
    ],
}


SYSTEM_PROMPT = """You are a real estate search query parser for Uzbekistan.
Your job is to extract structured search filters from natural language property queries.

The user may query in English, Russian, or Uzbek. Use the glossary below to understand Uzbek terms.

UZBEK REAL ESTATE GLOSSARY:
{glossary}

OUTPUT FORMAT:
You must return a JSON object with these fields (use null for unspecified values):
- rooms: integer or null (number of rooms)
- min_price: number or null (minimum price in USD)
- max_price: number or null (maximum price in USD)
- district: string or null (district name, always in English transliteration)
- proximity_to: string or null (one of: metro_station, bus_stop, park, school, supermarket, hospital)
- max_distance_m: integer or null (maximum distance to POI in meters, default 1000 if proximity mentioned)
- min_area_sqm: number or null (minimum area in square meters)
- max_area_sqm: number or null (maximum area in square meters)
- sort_by_comfort: string or null (one of: transport, shopping, education, green_space,
  safety, healthcare, entertainment, overall)

DISTRICT NAMES (use these exact spellings):
Yunusabad, Mirzo Ulugbek, Chilanzar, Sergeli, Shaykhantakhur, Yakkasaray,
Bektemir, Almazar, Uchtepa, Mirabad, Yashnabad, Olmazor

COMFORT CATEGORIES:
Use 'sort_by_comfort' when the user asks for the "best", "most", "top",
or a specific quality (e.g., "safest", "greenest", "near transport").
Available categories: transport, shopping, education, green_space, safety, healthcare, entertainment.

EXAMPLES:
Query: "2-room flat near metro under $70,000"
Answer: {{"rooms": 2, "max_price": 70000, "proximity_to": "metro_station", "max_distance_m": 1000,
"district": null, "min_price": null, "min_area_sqm": null, "max_area_sqm": null, "sort_by_comfort": "transport"}}

Query: "best green space 3 rooms"
Answer: {{"rooms": 3, "max_price": null, "proximity_to": null, "max_distance_m": null,
"district": null, "min_price": null, "min_area_sqm": null, "max_area_sqm": null, "sort_by_comfort": "green_space"}}

Query: "safest apartments in Yunusabad"
Answer: {{"rooms": null, "max_price": null, "proximity_to": null, "max_distance_m": null,
"district": "Yunusabad", "min_price": null, "min_area_sqm": null, "max_area_sqm": null, "sort_by_comfort": "safety"}}

Query: "квартира рядом с остановкой"
Answer: {{"rooms": null, "max_price": null, "proximity_to": "bus_stop", "max_distance_m": 1000,
"district": null, "min_price": null, "min_area_sqm": null, "max_area_sqm": null, "sort_by_comfort": "transport"}}

Return ONLY the JSON object, no other text."""


class AISearchService:
    """Service for AI-powered natural language property search."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.glossary = load_rag_context()

    async def parse_query(self, query: str) -> ParsedFilters:
        """
        Parse a natural language query into structured filters using GPT-4o-mini.

        Uses OpenAI's structured output with strict mode for guaranteed
        JSON schema compliance.
        """
        system_prompt = SYSTEM_PROMPT.format(glossary=self.glossary)

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=200,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from AI model")

            parsed = json.loads(content)
            return ParsedFilters(**parsed)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("AI model returned invalid JSON")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def execute_search(self, filters: ParsedFilters) -> list[Property]:
        """
        Execute a PostGIS spatial query based on the parsed filters.

        Combines B-tree index queries (price, rooms) with spatial
        proximity queries (ST_DWithin) for efficient filtering.
        """
        logger.info(
            "execute_search called with filters: %s",
            filters.model_dump(),
        )

        query = select(Property).where(Property.is_active == True)  # noqa: E712

        # Room count filter
        if filters.rooms is not None:
            query = query.where(Property.rooms == filters.rooms)

        # Price range filters
        if filters.min_price is not None:
            query = query.where(Property.price >= filters.min_price)
        if filters.max_price is not None:
            query = query.where(Property.price <= filters.max_price)

        # District filter — fuzzy ILIKE for transliteration tolerance
        if filters.district is not None:
            district_term = filters.district.strip()
            logger.info("Filtering by district ILIKE: %%%s%%", district_term)
            query = query.where(Property.district.ilike(f"%{district_term}%"))

        # Area range filters
        if filters.min_area_sqm is not None:
            query = query.where(Property.area_sqm >= filters.min_area_sqm)
        if filters.max_area_sqm is not None:
            query = query.where(Property.area_sqm <= filters.max_area_sqm)

        # Proximity to POI filter using PostGIS ST_DWithin
        if filters.proximity_to is not None:
            max_dist = filters.max_distance_m or 1000
            query = query.where(
                exists(
                    select(1)
                    .select_from(POI)
                    .where(
                        and_(
                            POI.category == filters.proximity_to,
                            func.ST_DWithin(
                                func.ST_Transform(Property.location, 3857),
                                func.ST_Transform(POI.location, 3857),
                                max_dist,
                            ),
                        )
                    )
                )
            )

        # Use selectinload to fetch comfort_score in a separate
        # query — avoids conflict with lazy="joined" default
        query = query.options(selectinload(Property.comfort_score))

        # Sorting logic
        if filters.sort_by_comfort:
            col_name = "overall_score" if filters.sort_by_comfort == "overall" else f"{filters.sort_by_comfort}_score"
            comfort_col = getattr(ComfortScore, col_name, None)
            if comfort_col is not None:
                # Join comfort_scores for ORDER BY
                query = query.outerjoin(
                    ComfortScore,
                    ComfortScore.property_id == Property.id,
                )
                # Use COALESCE so NULLs are treated as 0
                # and sink to the bottom
                query = query.order_by(
                    func.coalesce(comfort_col, 0).desc(),
                    Property.price.asc(),
                )
                logger.info("Sorting by comfort: %s DESC", col_name)
            else:
                logger.warning(
                    "Unknown comfort column: %s, falling back" " to price",
                    col_name,
                )
                query = query.order_by(Property.price.asc())
        else:
            query = query.order_by(Property.price.asc())

        # Limit results
        query = query.limit(50)

        result = await self.db.execute(query)
        properties = list(result.unique().scalars().all())

        logger.info(
            "Search returned %d properties (sort_by=%s)",
            len(properties),
            filters.sort_by_comfort,
        )

        # Debug: log top-3 property scores
        for p in properties[:3]:
            cs = p.comfort_score
            logger.info(
                "  -> %s | price=$%.0f | %s=%s",
                p.title[:40],
                float(p.price),
                filters.sort_by_comfort or "n/a",
                (
                    getattr(cs, f"{filters.sort_by_comfort}_score", None)
                    if cs and filters.sort_by_comfort
                    else (cs.overall_score if cs else "no_score")
                ),
            )

        return properties

    @staticmethod
    def infer_comfort_sort_from_proximity(filters: ParsedFilters) -> ParsedFilters:
        """
        Infer comfort sorting from proximity intent.

        If query asks for proximity (e.g. "near parks/schools"), rank by the
        corresponding comfort dimension unless sort is already explicit.
        """
        if filters.sort_by_comfort is not None:
            return filters
        if filters.proximity_to is None:
            return filters

        inferred_sort = PROXIMITY_TO_COMFORT_SORT_MAP.get(filters.proximity_to)
        if inferred_sort is None:
            return filters

        return filters.model_copy(update={"sort_by_comfort": inferred_sort})

    @staticmethod
    def infer_comfort_sort_from_query_text(query: str, filters: ParsedFilters) -> ParsedFilters:
        """
        Infer comfort sorting from plain-text intent keywords.

        This is a deterministic fallback for multilingual queries in case the
        LLM parser misses sort intent.
        """
        if filters.sort_by_comfort is not None:
            return filters

        normalized_query = re.sub(r"\s+", " ", query.lower()).strip()
        for comfort_dimension, keywords in COMFORT_QUERY_KEYWORDS.items():
            if any(keyword in normalized_query for keyword in keywords):
                return filters.model_copy(update={"sort_by_comfort": comfort_dimension})

        return filters

    async def search(self, query: str) -> tuple[ParsedFilters, list[Property]]:
        """
        Full search pipeline: parse query → execute spatial search.
        """
        filters = await self.parse_query(query)
        filters = self.infer_comfort_sort_from_proximity(filters)
        filters = self.infer_comfort_sort_from_query_text(query, filters)
        properties = await self.execute_search(filters)
        return filters, properties

    async def log_search_query(
        self,
        raw_query: str,
        parsed_filters: dict,
        result_count: int,
        processing_time_ms: int,
    ) -> None:
        """Log search query for analytics."""
        log_entry = SearchQuery(
            raw_query=raw_query,
            parsed_filters=parsed_filters,
            result_count=result_count,
            processing_time_ms=processing_time_ms,
            parse_success=True,
        )
        self.db.add(log_entry)
        await self.db.flush()
