from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class QuoteLineOutNested(BaseModel):
    id: int
    quote_structure_item_id: int
    quote_structure_item_name: str = ""
    amount: Optional[float] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class QuoteApartmentOut(BaseModel):
    id: int
    quote_building_id: int
    size_sqm: float
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteBuildingCreate(BaseModel):
    address: Optional[str] = None
    num_residents: Optional[int] = None
    calculation_method: str = "by_residents"
    sort_order: int = 0


class QuoteBuildingUpdate(BaseModel):
    address: Optional[str] = None
    num_residents: Optional[int] = None
    calculation_method: Optional[str] = None
    sort_order: Optional[int] = None


class QuoteBuildingOut(BaseModel):
    id: int
    quote_project_id: int
    address: Optional[str] = None
    num_residents: Optional[int] = None
    calculation_method: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
    quote_lines: List[QuoteLineOutNested] = []
    quote_apartments: List[QuoteApartmentOut] = []

    model_config = ConfigDict(from_attributes=True)


class QuoteApartmentsBulkCreate(BaseModel):
    count: int
    size_sqm: float = 0.0
