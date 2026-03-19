"""Area model - represents a geographic area or zone for asset management."""
import uuid
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.cems.models.base import CEMSBase, TimestampMixin, UUIDPrimaryKeyMixin


class Area(UUIDPrimaryKeyMixin, TimestampMixin, CEMSBase):
    """Represents a geographic area or zone for organizing assets and warehouses."""
    __tablename__ = "cems_areas"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
