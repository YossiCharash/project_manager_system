"""
Admin Invite Service - manages admin invite codes.
"""
from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.invite import Invite
from backend.repositories.user_repository import UserRepository
from backend.core.security import hash_password
from backend.models.user import UserRole

logger = logging.getLogger(__name__)


class AdminInviteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invite(self, invite_data, created_by: int) -> Invite:
        invite = Invite.create_admin_invite(
            email=invite_data.email,
            full_name=invite_data.full_name,
            created_by=created_by,
            expires_days=getattr(invite_data, 'expires_days', 7),
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def list_invites(self, created_by: Optional[int] = None) -> list[Invite]:
        from typing import Optional
        result = await self.db.execute(
            select(Invite)
            .where(Invite.invite_type == "admin")
            .order_by(Invite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_invite_by_code(self, invite_code: str) -> Invite:
        result = await self.db.execute(
            select(Invite).where(
                Invite.invite_token == invite_code,
                Invite.invite_type == "admin"
            )
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        return invite

    async def delete_invite(self, invite_id: int, deleted_by: int) -> None:
        result = await self.db.execute(
            select(Invite).where(Invite.id == invite_id, Invite.invite_type == "admin")
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        await self.db.delete(invite)
        await self.db.commit()

    async def use_invite(self, invite_data) -> object:
        invite_code = getattr(invite_data, 'invite_code', None) or getattr(invite_data, 'invite_token', None)
        result = await self.db.execute(
            select(Invite).where(
                Invite.invite_token == invite_code,
                Invite.invite_type == "admin"
            )
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        if invite.is_used:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
        if invite.is_expired():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired")

        from backend.models.user import User
        user_repo = UserRepository(self.db)
        existing = await user_repo.get_by_email(invite.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        user = User(
            email=invite.email,
            full_name=invite.full_name,
            password_hash=hash_password(invite_data.password),
            role=UserRole.ADMIN.value,
            email_verified=True,
        )
        created_user = await user_repo.create(user)

        from datetime import datetime, timezone
        invite.is_used = True
        invite.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.commit()

        return created_user
