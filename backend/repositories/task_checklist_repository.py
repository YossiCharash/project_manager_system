from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.task import TaskChecklistItem
from backend.repositories.base import BaseRepository


class TaskChecklistRepository(BaseRepository[TaskChecklistItem]):
    model = TaskChecklistItem

    async def list_for_task(self, task_id: int) -> list[TaskChecklistItem]:
        result = await self.db.execute(
            select(TaskChecklistItem)
            .options(
                selectinload(TaskChecklistItem.assigned_user),
                selectinload(TaskChecklistItem.handled_by_user),
            )
            .where(TaskChecklistItem.task_id == task_id)
            .order_by(TaskChecklistItem.sort_order, TaskChecklistItem.id)
        )
        return list(result.unique().scalars().all())

    async def get_by_id(self, item_id: int) -> Optional[TaskChecklistItem]:
        result = await self.db.execute(
            select(TaskChecklistItem)
            .options(
                selectinload(TaskChecklistItem.assigned_user),
                selectinload(TaskChecklistItem.handled_by_user),
            )
            .where(TaskChecklistItem.id == item_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_next_sort_order(self, task_id: int) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.coalesce(func.max(TaskChecklistItem.sort_order), -1))
            .where(TaskChecklistItem.task_id == task_id)
        )
        return (result.scalar_one() or -1) + 1

    async def get_summary(self, task_id: int) -> dict:
        """Return {total, completed} counts for a task's checklist."""
        from sqlalchemy import func, case
        result = await self.db.execute(
            select(
                func.count(TaskChecklistItem.id).label("total"),
                func.sum(
                    case((TaskChecklistItem.is_completed == True, 1), else_=0)  # noqa: E712
                ).label("completed"),
            ).where(TaskChecklistItem.task_id == task_id)
        )
        row = result.one()
        return {"total": row.total or 0, "completed": int(row.completed or 0)}

    async def create(self, item: TaskChecklistItem) -> TaskChecklistItem:
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        refreshed = await self.get_by_id(item.id)
        return refreshed or item

    async def update(self, item: TaskChecklistItem) -> TaskChecklistItem:
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: TaskChecklistItem) -> None:
        await self.db.delete(item)
        await self.db.flush()
