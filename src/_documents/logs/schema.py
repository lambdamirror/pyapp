from datetime import date as dateType
from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, Field

from utils.helper import TIMEZONE_OFFSET
from utils.schema import BaseConfig, PyObjectId


class Action(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    call_type: Union[None, str]
    ip_address: Union[None, str]
    user_agent: Union[None, str]
    user_id: Union[None, str]
    user_email: Union[None, str]
    method: Union[None, str]
    url: Union[None, str]
    path_params: Union[None, dict]
    query_params: Union[None, dict]
    body: Union[None, dict, List]
    refs: Union[None, str, List[str]]

    class Config(BaseConfig):
        pass


class Log(BaseModel):
    id: PyObjectId = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(datetime.utcnow().strftime("%Y-%m-%d"))
    action: List[Action]

    class Config(BaseConfig):
        pass