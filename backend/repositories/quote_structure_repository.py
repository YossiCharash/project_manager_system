from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.quote_structure_item import QuoteStructureItem
from backend.repositories.base import BaseRepository


class QuoteStructureRepository(BaseRepository[QuoteStructureItem]):
    model = QuoteStructureItem

    async def list(self, include_inactive: bool = False) -> list[QuoteStructureItem]:
        stmt = select(QuoteStructureItem).order_by(QuoteStructureItem.sort_order, QuoteStructureItem.id)
        if not include_inactive:
            stmt = stmt.where(QuoteStructureItem.is_active == True)  # noqa: E712
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
