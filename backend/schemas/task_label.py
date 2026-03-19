from typing import Optional
from pydantic import BaseModel, ConfigDict


class TaskLabelCreate(BaseModel):
    name: str
    color: Optional[str] = None


class TaskLabelUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class TaskLabelOut(BaseModel):
    id: int
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)
