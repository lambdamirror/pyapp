import collections
from datetime import datetime, timedelta, timezone
from enum import Enum
from queue import Queue
from typing import Any

import numpy as np
from bson import ObjectId
from ordered_set import OrderedSet
from pydantic import AnyUrl, BaseModel, EmailStr, Field

DATABASE_TYPES = {
    'Boolean': lambda x: True if str(x).lower() == 'true' else 'false',
    'String': lambda x: str(x),
    'String Array': lambda x: [str(v) for v in x],
    'Integer': lambda x: int(x),
    'Integer Array': lambda x: [int(v) for v in x],
    'Float': lambda x: float(x),
    'Float Array': lambda x: [int(v) for v in x],
    'Select': lambda x: x,
}


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class OrderedSetQueue(Queue):
    def _init(self, maxsize):
        self.queue = OrderedSet()
    def _put(self, item):
        self.queue.add(item)
    def _get(self):
        return self.queue.pop()


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseConfig():
    allow_population_by_field_name = True
    arbitrary_types_allowed = True
    json_encoders = {
        ObjectId: str,
        datetime: lambda v: v.replace(tzinfo=timezone.utc).timestamp(),
        np.int64: int
    }

class UserActivity(BaseModel):
    user: PyObjectId | str
    time: datetime = Field(default_factory=datetime.utcnow)

    class Config(BaseConfig):
        pass

class Quote(BaseModel):
    amount: float | None
    currency: str | None
    converted_amount: float | None
    
    class Config(BaseConfig):
        pass


class UserQuote(BaseModel):
    user: PyObjectId | None
    description: str | None

    class Config(BaseConfig):
        pass

class Extra(UserQuote):
    type: str


class KeyValue(BaseModel):
    key: str
    value: Any

    class Config(BaseConfig):
        pass
