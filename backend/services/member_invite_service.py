"""
Member Invite Service - manages member registration invites.
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


class MemberInviteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invite(self, invite_data, created_by: int) -> Invite:
        invite = Invite.create_member_invite(
            email=invite_data.email,
            full_name=invite_data.full_name,
            created_by=created_by,
            group_id=getattr(invite_data, 'group_id', None),
            expires_days=getattr(invite_data, 'expires_days', 7),
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)

        # Send registration email
        try:
            from backend.services.email_service import EmailService
            email_service = EmailService()
            await email_service.send_member_invite_email(
                email=invite.email,
                full_name=invite.full_name,
                invite_token=invite.invite_token,
            )
        except Exception:
            logger.warning("Failed to send member invite email", exc_info=True)

        return invite

    async def list_invites(self) -> list[Invite]:
        result = await self.db.execute(
            select(Invite)
            .where(Invite.invite_type == "member")
            .order_by(Invite.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_invite_by_token(self, invite_token: str) -> Invite:
        result = await self.db.execute(
            select(Invite).where(
                Invite.invite_token == invite_token,
                Invite.invite_type == "member"
            )
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        return invite

    async def delete_invite(self, invite_id: int) -> None:
        result = await self.db.execute(
            select(Invite).where(Invite.id == invite_id, Invite.invite_type == "member")
        )
        invite = result.scalar_one_or_none()
        if not invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        await self.db.delete(invite)
        await self.db.commit()

    async def use_invite(self, invite_data) -> object:
        invite_token = invite_data.invite_token
        result = await self.db.execute(
            select(Invite).where(
                Invite.invite_token == invite_token,
                Invite.invite_type == "member"
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
            role=UserRole.MEMBER.value,
            group_id=invite.group_id,
            email_verified=True,
        )
        created_user = await user_repo.create(user)

        from datetime import datetime, timezone
        invite.is_used = True
        invite.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.commit()

        return created_user
