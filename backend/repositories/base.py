from __future__ import annotations
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository.

    Subclasses declare a ``model`` class attribute pointing to the SQLAlchemy
    model class.  The constructor accepts an ``AsyncSession`` and exposes it as
    ``self.db`` so domain-specific query methods can use it directly.

    Usage::

        class UserRepository(BaseRepository[User]):
            model = User

        repo = UserRepository(db)
        user = await repo.get_by_id(1)
    """

    model: Type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> Optional[ModelT]:
        return await self.db.get(self.model, entity_id)

    # Alias used by some repositories (e.g. SupplierRepository.get)
    async def get(self, entity_id: int) -> Optional[ModelT]:
        return await self.get_by_id(entity_id)

    async def create(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.db.delete(entity)
        await self.db.commit()
