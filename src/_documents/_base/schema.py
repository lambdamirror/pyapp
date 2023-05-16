from datetime import datetime, timedelta
from typing import Any, Union, List

from _services.mongo.service import MongoDbClient

from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field


class ServiceBaseConfig(BaseModel):
    document: str
    record_status: List[str] = Field([])
    py_list_class: Any
    py_create_class: Any
    py_master_class: Any
    py_update_class: Any
    
    mongodb_client: Union[None, MongoDbClient]

    class Config(BaseConfig):
        pass


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
