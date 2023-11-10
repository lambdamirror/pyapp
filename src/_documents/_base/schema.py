from datetime import datetime, timedelta
from typing import Any, List

from _services.mongo.client import MongoDbClient

from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field


class ServiceBaseConfig(BaseModel):
    document: str
    record_status: List[str] = Field([])
    py_list_class: Any
    py_create_class: Any
    py_master_class: Any
    py_update_class: Any
    
    mongodb_client: MongoDbClient | None

    class Config(BaseConfig):
        pass

class SearchKeyword(BaseModel):
    field: str
    key: str

class BaseCreate(BaseModel):
    id: PyObjectId

    class Config(BaseConfig):
        pass


class BaseUpdate(BaseModel):
    id: PyObjectId

    class Config(BaseConfig):
        pass


class BaseList(BaseModel):
    id: PyObjectId

    class Config(BaseConfig):
        pass


class BaseMaster(BaseList):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
