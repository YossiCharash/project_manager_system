from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class QuoteSubjectCreate(BaseModel):
    address: Optional[str] = None
    num_apartments: Optional[int] = None
    num_buildings: Optional[int] = None
    notes: Optional[str] = None


class QuoteSubjectUpdate(BaseModel):
    address: Optional[str] = None
    num_apartments: Optional[int] = None
    num_buildings: Optional[int] = None
    notes: Optional[str] = None


class QuoteSubjectOut(BaseModel):
    id: int
    address: Optional[str] = None
    num_apartments: Optional[int] = None
    num_buildings: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
