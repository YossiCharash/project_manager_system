from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class QuoteStructureItemCreate(BaseModel):
    name: str
    sort_order: int = 0


class QuoteStructureItemUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class QuoteStructureItemOut(BaseModel):
    id: int
    name: str
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
