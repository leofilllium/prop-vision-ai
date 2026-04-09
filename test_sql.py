import asyncio
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.services.ai_search_service import AISearchService
from app.schemas.search import ParsedFilters
from sqlalchemy.dialects import postgresql

settings = get_settings()

async def main():
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        ai_service = AISearchService(db)
        filters = ParsedFilters(proximity_to="metro_station", max_distance_m=1000)
        
        # Get the query
        from sqlalchemy import select, func
        from app.models.property import Property
        from app.models.poi import POI
        from geoalchemy2 import Geography
        
        query = select(Property).where(Property.is_active == True)
        poi_subquery = select(POI.location).where(POI.category == filters.proximity_to).subquery()
        query = query.where(
            func.ST_DWithin(
                func.cast(Property.location, Geography),
                func.cast(poi_subquery.c.location, Geography),
                1000,
            )
        )
        
        print("Generated SQL:")
        print(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))

if __name__ == "__main__":
    asyncio.run(main())
