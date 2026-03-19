from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.quote_building import QuoteBuilding, QuoteApartment
from backend.repositories.base import BaseRepository


class QuoteBuildingRepository(BaseRepository[QuoteBuilding]):
    model = QuoteBuilding

    async def get(self, building_id: int) -> Optional[QuoteBuilding]:
        from backend.models.quote_line import QuoteLine
        result = await self.db.execute(
            select(QuoteBuilding)
            .options(
                selectinload(QuoteBuilding.quote_lines).selectinload(QuoteLine.quote_structure_item),
                selectinload(QuoteBuilding.quote_apartments),
            )
            .where(QuoteBuilding.id == building_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_by_quote_project(self, quote_project_id: int) -> list[QuoteBuilding]:
        from backend.models.quote_line import QuoteLine
        result = await self.db.execute(
            select(QuoteBuilding)
            .options(
                selectinload(QuoteBuilding.quote_lines).selectinload(QuoteLine.quote_structure_item),
                selectinload(QuoteBuilding.quote_apartments),
            )
            .where(QuoteBuilding.quote_project_id == quote_project_id)
            .order_by(QuoteBuilding.sort_order, QuoteBuilding.id)
        )
        return list(result.unique().scalars().all())


class QuoteApartmentRepository(BaseRepository[QuoteApartment]):
    model = QuoteApartment

    async def list_by_building(self, building_id: int) -> list[QuoteApartment]:
        result = await self.db.execute(
            select(QuoteApartment)
            .where(QuoteApartment.quote_building_id == building_id)
            .order_by(QuoteApartment.sort_order, QuoteApartment.id)
        )
        return list(result.scalars().all())
