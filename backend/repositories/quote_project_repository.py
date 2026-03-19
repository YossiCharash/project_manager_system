from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.quote_project import QuoteProject
from backend.repositories.base import BaseRepository


class QuoteProjectRepository(BaseRepository[QuoteProject]):
    model = QuoteProject

    async def get(self, quote_project_id: int) -> Optional[QuoteProject]:
        result = await self.db.execute(
            select(QuoteProject)
            .options(
                selectinload(QuoteProject.children),
                selectinload(QuoteProject.quote_lines).selectinload(
                    __import__('backend.models.quote_line', fromlist=['QuoteLine']).QuoteLine.quote_structure_item
                ),
                selectinload(QuoteProject.quote_buildings).selectinload(
                    __import__('backend.models.quote_building', fromlist=['QuoteBuilding']).QuoteBuilding.quote_lines
                ).selectinload(
                    __import__('backend.models.quote_line', fromlist=['QuoteLine']).QuoteLine.quote_structure_item
                ),
                selectinload(QuoteProject.quote_buildings).selectinload(
                    __import__('backend.models.quote_building', fromlist=['QuoteBuilding']).QuoteBuilding.quote_apartments
                ),
                selectinload(QuoteProject.quote_subject),
            )
            .where(QuoteProject.id == quote_project_id)
        )
        return result.unique().scalar_one_or_none()

    async def list(
        self,
        parent_id: Optional[int] = None,
        project_id: Optional[int] = None,
        quote_subject_id: Optional[int] = None,
        status: Optional[str] = None,
        include_all: bool = False,
    ) -> list[QuoteProject]:
        from backend.models.quote_line import QuoteLine
        from backend.models.quote_building import QuoteBuilding
        stmt = (
            select(QuoteProject)
            .options(
                selectinload(QuoteProject.children),
                selectinload(QuoteProject.quote_lines).selectinload(QuoteLine.quote_structure_item),
                selectinload(QuoteProject.quote_buildings).selectinload(QuoteBuilding.quote_lines).selectinload(QuoteLine.quote_structure_item),
                selectinload(QuoteProject.quote_buildings).selectinload(QuoteBuilding.quote_apartments),
                selectinload(QuoteProject.quote_subject),
            )
            .order_by(QuoteProject.created_at.desc())
        )
        if not include_all:
            if parent_id is not None:
                stmt = stmt.where(QuoteProject.parent_id == parent_id)
            if project_id is not None:
                stmt = stmt.where(QuoteProject.project_id == project_id)
            if quote_subject_id is not None:
                stmt = stmt.where(QuoteProject.quote_subject_id == quote_subject_id)
        if status is not None:
            stmt = stmt.where(QuoteProject.status == status)
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_children_count(self, quote_project_id: int) -> int:
        result = await self.db.execute(
            select(func.count(QuoteProject.id)).where(QuoteProject.parent_id == quote_project_id)
        )
        return result.scalar_one() or 0
