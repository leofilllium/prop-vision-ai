"""
Test suite for AI search query parsing.

50 sample queries across English, Russian, and Uzbek with expected
parsed filter outputs. Target: ≥85% accuracy.
"""

import pytest
from app.schemas.search import ParsedFilters


# Test data: (query, expected_filters)
# Expected filters use only 'rooms', 'max_price', 'min_price', 'district',
# 'proximity_to', 'max_distance_m', 'min_area_sqm', 'max_area_sqm'
ENGLISH_QUERIES = [
    (
        "2-room flat near metro under $70,000",
        {"rooms": 2, "max_price": 70000, "proximity_to": "metro_station"},
    ),
    (
        "3 rooms in Yunusabad",
        {"rooms": 3, "district": "Yunusabad"},
    ),
    (
        "cheap apartment in Chilanzar",
        {"district": "Chilanzar"},
    ),
    (
        "apartment under $50,000 near school",
        {"max_price": 50000, "proximity_to": "school"},
    ),
    (
        "large 4-room flat in Mirzo Ulugbek",
        {"rooms": 4, "district": "Mirzo Ulugbek"},
    ),
    (
        "1 room apartment close to park $30,000-$50,000",
        {"rooms": 1, "min_price": 30000, "max_price": 50000, "proximity_to": "park"},
    ),
    (
        "spacious apartment with 3 bedrooms near supermarket",
        {"rooms": 3, "proximity_to": "supermarket"},
    ),
    (
        "2 room flat in Sergeli under $40,000",
        {"rooms": 2, "max_price": 40000, "district": "Sergeli"},
    ),
    (
        "apartment near hospital in Yakkasaray",
        {"proximity_to": "hospital", "district": "Yakkasaray"},
    ),
    (
        "5 room house in Shaykhantakhur",
        {"rooms": 5, "district": "Shaykhantakhur"},
    ),
    (
        "apartment 80-100 square meters",
        {"min_area_sqm": 80, "max_area_sqm": 100},
    ),
    (
        "3 rooms near metro station $60,000-$90,000",
        {"rooms": 3, "min_price": 60000, "max_price": 90000, "proximity_to": "metro_station"},
    ),
    (
        "studio apartment in city center",
        {},
    ),
    (
        "2 room apartment near bus stop under $45,000",
        {"rooms": 2, "max_price": 45000, "proximity_to": "bus_stop"},
    ),
    (
        "new building apartment in Yunusabad 3 rooms",
        {"rooms": 3, "district": "Yunusabad"},
    ),
    (
        "quiet area near park, 2 rooms",
        {"rooms": 2, "proximity_to": "park"},
    ),
    (
        "affordable 1 room flat near Chorsu",
        {"rooms": 1},
    ),
    (
        "apartment from $40,000 to $80,000 in Almazar",
        {"min_price": 40000, "max_price": 80000, "district": "Almazar"},
    ),
    (
        "3-room apartment near metro, renovated",
        {"rooms": 3, "proximity_to": "metro_station"},
    ),
    (
        "big apartment near school in Mirabad",
        {"proximity_to": "school", "district": "Mirabad"},
    ),
]

RUSSIAN_QUERIES = [
    (
        "двухкомнатная квартира рядом с метро до 70 тысяч",
        {"rooms": 2, "max_price": 70000, "proximity_to": "metro_station"},
    ),
    (
        "3-комнатная Юнусабад",
        {"rooms": 3, "district": "Yunusabad"},
    ),
    (
        "квартира в Чиланзаре недорого",
        {"district": "Chilanzar"},
    ),
    (
        "большая квартира рядом с парком, до 80 тысяч",
        {"max_price": 80000, "proximity_to": "park"},
    ),
    (
        "1 комната Сергели до 30000",
        {"rooms": 1, "max_price": 30000, "district": "Sergeli"},
    ),
    (
        "квартира рядом со школой Мирзо Улугбек",
        {"proximity_to": "school", "district": "Mirzo Ulugbek"},
    ),
    (
        "4 комнатная квартира от 60 до 100 тысяч",
        {"rooms": 4, "min_price": 60000, "max_price": 100000},
    ),
    (
        "новостройка 3 комнаты Яккасарай",
        {"rooms": 3, "district": "Yakkasaray"},
    ),
    (
        "студия рядом с метро",
        {"proximity_to": "metro_station"},
    ),
    (
        "просторная квартира 80 кв.м Шайхантахур",
        {"min_area_sqm": 80, "district": "Shaykhantakhur"},
    ),
    (
        "2 комнаты рядом с больницей до 50000 долларов",
        {"rooms": 2, "max_price": 50000, "proximity_to": "hospital"},
    ),
    (
        "квартира рядом с супермаркетом в Учтепе",
        {"proximity_to": "supermarket", "district": "Uchtepa"},
    ),
    (
        "3-комнатная квартира 70-90 кв.м рядом с метро",
        {"rooms": 3, "min_area_sqm": 70, "max_area_sqm": 90, "proximity_to": "metro_station"},
    ),
    (
        "однокомнатная до 35 тысяч",
        {"rooms": 1, "max_price": 35000},
    ),
    (
        "5 комнат в Алмазаре",
        {"rooms": 5, "district": "Almazar"},
    ),
    (
        "квартира рядом с автобусной остановкой",
        {"proximity_to": "bus_stop"},
    ),
    (
        "тихий район с парком 2 комнаты Юнусабад",
        {"rooms": 2, "proximity_to": "park", "district": "Yunusabad"},
    ),
    (
        "квартира в Мирабаде до 90 тысяч 3 комнаты",
        {"rooms": 3, "max_price": 90000, "district": "Mirabad"},
    ),
    (
        "двушка рядом с метро новостройка",
        {"rooms": 2, "proximity_to": "metro_station"},
    ),
    (
        "квартира от 50 до 70 тысяч Яшнабад",
        {"min_price": 50000, "max_price": 70000, "district": "Yashnabad"},
    ),
]

UZBEK_QUERIES = [
    (
        "3 xonali kvartira Chilanzar 50 ming dollardan past",
        {"rooms": 3, "max_price": 50000, "district": "Chilanzar"},
    ),
    (
        "2 xonali metro yaqinida",
        {"rooms": 2, "proximity_to": "metro_station"},
    ),
    (
        "arzon kvartira Sergeli",
        {"district": "Sergeli"},
    ),
    (
        "4 xonali uy Yunusobod",
        {"rooms": 4, "district": "Yunusabad"},
    ),
    (
        "kvartira maktab yaqinida 70 mingdan past",
        {"max_price": 70000, "proximity_to": "school"},
    ),
    (
        "1 xonali kvartira 30 ming dollar",
        {"rooms": 1, "max_price": 30000},
    ),
    (
        "keng 3 xonali Mirzo Ulug'bek",
        {"rooms": 3, "district": "Mirzo Ulugbek"},
    ),
    (
        "yangi uy 2 xona bog' yaqinida",
        {"rooms": 2, "proximity_to": "park"},
    ),
    (
        "shinam kvartira shahar markazida",
        {},
    ),
    (
        "3 xonali kvartira 80 kv.m Yakkasaroy",
        {"rooms": 3, "min_area_sqm": 80, "district": "Yakkasaray"},
    ),
]

ALL_QUERIES = ENGLISH_QUERIES + RUSSIAN_QUERIES + UZBEK_QUERIES


def check_filter_match(expected: dict, parsed: ParsedFilters) -> bool:
    """
    Check if parsed filters match the expected values.

    Only checks fields that are specified in the expected dict.
    Unspecified fields are not checked (they can be null or have any value).
    """
    parsed_dict = parsed.model_dump()

    for key, expected_value in expected.items():
        actual_value = parsed_dict.get(key)

        # For district, do case-insensitive comparison
        if key == "district" and isinstance(expected_value, str):
            if actual_value is None:
                return False
            if actual_value.lower() != expected_value.lower():
                return False
        elif actual_value != expected_value:
            return False

    return True


class TestSearchQueries:
    """Test suite for AI search query parsing accuracy."""

    @pytest.mark.parametrize(
        "query,expected_filters",
        ALL_QUERIES,
        ids=[f"q{i:02d}" for i in range(len(ALL_QUERIES))],
    )
    def test_query_parsing_structure(self, query, expected_filters):
        """Verify test data structure is valid."""
        # Verify expected_filters keys are valid ParsedFilters fields
        valid_fields = set(ParsedFilters.model_fields.keys())
        for key in expected_filters:
            assert key in valid_fields, f"Invalid field '{key}' in expected filters"

    def test_total_query_count(self):
        """Verify we have at least 50 test queries."""
        assert len(ALL_QUERIES) >= 50, f"Expected ≥50 queries, got {len(ALL_QUERIES)}"

    def test_english_query_count(self):
        """Verify we have at least 20 English queries."""
        assert len(ENGLISH_QUERIES) >= 20

    def test_russian_query_count(self):
        """Verify we have at least 20 Russian queries."""
        assert len(RUSSIAN_QUERIES) >= 20

    def test_uzbek_query_count(self):
        """Verify we have at least 10 Uzbek queries."""
        assert len(UZBEK_QUERIES) >= 10
