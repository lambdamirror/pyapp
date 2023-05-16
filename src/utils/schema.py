import collections
from datetime import datetime, timedelta, timezone
from enum import Enum
from queue import Queue
from typing import List, Union

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


# class OrderedSet(collections):

#     def __init__(self, iterable=None):
#         self.end = end = [] 
#         end += [None, end, end]         # sentinel node for doubly linked list
#         self.map = {}                   # key --> [key, prev, next]
#         if iterable is not None:
#             self |= iterable

#     def __len__(self):
#         return len(self.map)

#     def __contains__(self, key):
#         return key in self.map

#     def add(self, key):
#         if key not in self.map:
#             end = self.end
#             curr = end[1]
#             curr[2] = end[1] = self.map[key] = [key, curr, end]

#     def discard(self, key):
#         if key in self.map:        
#             key, prev, next = self.map.pop(key)
#             prev[2] = next
#             next[1] = prev

#     def __iter__(self):
#         end = self.end
#         curr = end[2]
#         while curr is not end:
#             yield curr[0]
#             curr = curr[2]

#     def __reversed__(self):
#         end = self.end
#         curr = end[1]
#         while curr is not end:
#             yield curr[0]
#             curr = curr[1]

#     def pop(self, last=True):
#         if not self:
#             raise KeyError('set is empty')
#         key = self.end[1][0] if last else self.end[2][0]
#         self.discard(key)
#         return key

#     def __repr__(self):
#         if not self:
#             return '%s()' % (self.__class__.__name__,)
#         return '%s(%r)' % (self.__class__.__name__, list(self))

#     def __eq__(self, other):
#         if isinstance(other, OrderedSet):
#             return len(self) == len(other) and list(self) == list(other)


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


class CurrencyAmount(BaseModel):
    user: Union[None, PyObjectId]
    description: Union[None, str]
    amount: float = Field(0)
    currency: Union[None, str]
    converted_amount: Union[None, float]
    
    class Config(BaseConfig):
        pass


class Extra(CurrencyAmount):
    type: str

