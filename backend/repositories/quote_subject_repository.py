from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.quote_subject import QuoteSubject
from backend.repositories.base import BaseRepository


class QuoteSubjectRepository(BaseRepository[QuoteSubject]):
    model = QuoteSubject

    async def list(self) -> list[QuoteSubject]:
        result = await self.db.execute(
            select(QuoteSubject).order_by(QuoteSubject.created_at.desc())
        )
        return list(result.scalars().all())
