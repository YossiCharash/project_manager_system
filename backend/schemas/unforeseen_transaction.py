from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class UnforeseenTransactionLineCreate(BaseModel):
    line_type: str  # 'expense' or 'income'
    amount: float
    description: Optional[str] = None


class UnforeseenTransactionCreate(BaseModel):
    project_id: int
    contract_period_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: Optional[date] = None
    lines: Optional[List[UnforeseenTransactionLineCreate]] = None


class UnforeseenTransactionUpdate(BaseModel):
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: Optional[date] = None
    status: Optional[str] = None
    lines: Optional[List[UnforeseenTransactionLineCreate]] = None


class UnforeseenTransactionOut(BaseModel):
    id: int
    project_id: int
    contract_period_id: Optional[int] = None
    status: str
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: date
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
