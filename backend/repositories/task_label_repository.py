from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.task import TaskLabel
from backend.repositories.base import BaseRepository


class TaskLabelRepository(BaseRepository[TaskLabel]):
    model = TaskLabel

    async def list_all(self) -> list[TaskLabel]:
        result = await self.db.execute(
            select(TaskLabel).order_by(TaskLabel.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, label_id: int) -> Optional[TaskLabel]:
        return await self.db.get(TaskLabel, label_id)

    async def get_by_ids(self, label_ids: list[int]) -> list[TaskLabel]:
        if not label_ids:
            return []
        result = await self.db.execute(
            select(TaskLabel).where(TaskLabel.id.in_(label_ids))
        )
        return list(result.scalars().all())

    async def delete(self, label: TaskLabel) -> None:
        await self.db.delete(label)
        await self.db.flush()
