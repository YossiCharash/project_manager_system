from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class QuoteLineCreate(BaseModel):
    quote_structure_item_id: int
    quote_building_id: Optional[int] = None
    amount: Optional[float] = None
    sort_order: int = 0


class QuoteLineUpdate(BaseModel):
    amount: Optional[float] = None
    sort_order: Optional[int] = None


class QuoteLineOut(BaseModel):
    id: int
    quote_project_id: Optional[int] = None
    quote_structure_item_id: int
    quote_structure_item_name: str = ""
    amount: Optional[float] = None
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
