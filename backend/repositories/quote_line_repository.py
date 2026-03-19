from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.quote_line import QuoteLine
from backend.repositories.base import BaseRepository


class QuoteLineRepository(BaseRepository[QuoteLine]):
    model = QuoteLine

    async def get(self, line_id: int) -> Optional[QuoteLine]:
        result = await self.db.execute(
            select(QuoteLine)
            .options(selectinload(QuoteLine.quote_structure_item))
            .where(QuoteLine.id == line_id)
        )
        return result.unique().scalar_one_or_none()

    async def list_by_quote_project(self, quote_project_id: int) -> list[QuoteLine]:
        result = await self.db.execute(
            select(QuoteLine)
            .options(selectinload(QuoteLine.quote_structure_item))
            .where(QuoteLine.quote_project_id == quote_project_id)
            .order_by(QuoteLine.sort_order, QuoteLine.id)
        )
        return list(result.unique().scalars().all())
