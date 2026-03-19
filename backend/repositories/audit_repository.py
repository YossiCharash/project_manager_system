from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.audit_log import AuditLog
from backend.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: Optional[int] = None,
        entity: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        exclude_action: Optional[str] = None,
    ) -> list[AuditLog]:
        conditions = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if entity is not None:
            conditions.append(AuditLog.entity == entity)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if start_date is not None:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(AuditLog.created_at <= end_date)
        if exclude_action is not None:
            conditions.append(AuditLog.action != exclude_action)

        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        user_id: Optional[int] = None,
        entity: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        exclude_action: Optional[str] = None,
    ) -> int:
        from sqlalchemy import func
        conditions = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if entity is not None:
            conditions.append(AuditLog.entity == entity)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if start_date is not None:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date is not None:
            conditions.append(AuditLog.created_at <= end_date)
        if exclude_action is not None:
            conditions.append(AuditLog.action != exclude_action)

        stmt = select(func.count(AuditLog.id))
        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.db.execute(stmt)
        return result.scalar_one() or 0
