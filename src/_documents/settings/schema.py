from datetime import datetime
from typing import Any

from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field


class SettingCreate(BaseModel):
    group: str | None 
    key: str
    value: Any

    class Config(BaseConfig):
        pass


class SettingUpdate(SettingCreate):
    id: PyObjectId | None 


class SettingList(SettingUpdate):
    id: PyObjectId = Field(None, alias="_id")
    created_at: datetime | None 
    modified_at: datetime | None 
    key: str | None 


class Setting(SettingList):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)