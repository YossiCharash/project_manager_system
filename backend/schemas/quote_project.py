from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from backend.schemas.quote_subject import QuoteSubjectOut


class QuoteLineOutNested(BaseModel):
    id: int
    quote_structure_item_id: int
    quote_structure_item_name: str = ""
    amount: Optional[float] = None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class QuoteProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: Optional[int] = None
    quote_subject_id: Optional[int] = None
    expected_start_date: Optional[date] = None
    expected_income: Optional[float] = None
    expected_expenses: Optional[float] = None
    num_residents: Optional[int] = None


class QuoteProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: Optional[int] = None
    expected_start_date: Optional[date] = None
    expected_income: Optional[float] = None
    expected_expenses: Optional[float] = None
    num_residents: Optional[int] = None


class QuoteProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    project_id: Optional[int] = None
    quote_subject_id: Optional[int] = None
    expected_start_date: Optional[date] = None
    expected_income: Optional[float] = None
    expected_expenses: Optional[float] = None
    num_residents: Optional[int] = None
    status: str
    converted_project_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    quote_lines: List[QuoteLineOutNested] = []
    children_count: int = 0
    quote_buildings: List = []
    quote_subject: Optional[QuoteSubjectOut] = None

    model_config = ConfigDict(from_attributes=True)
