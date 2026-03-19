from datetime import datetime
from typing import Optional, Any, List
from pydantic import BaseModel, ConfigDict


class GroupTransactionDraftCreate(BaseModel):
    name: Optional[str] = None
    rows: Optional[List[Any]] = None


class GroupTransactionDraftUpdate(BaseModel):
    name: Optional[str] = None
    rows: Optional[List[Any]] = None


class GroupTransactionDraftOut(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    rows: List[Any] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
