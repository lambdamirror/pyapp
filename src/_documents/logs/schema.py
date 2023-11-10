from datetime import date as dateType
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from utils.helper import TIMEZONE_OFFSET
from utils.schema import BaseConfig, PyObjectId


class Action(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    call_type: str | None 
    ip_address: str | None 
    user_agent: str | None 
    user_id: str | None 
    user_email: str | None 
    method: str | None 
    url: str | None 
    path_params: dict | None 
    query_params: dict | None 
    body: dict | List | None 
    refs: str | List[str] | None 

    class Config(BaseConfig):
        pass


class Log(BaseModel):
    id: PyObjectId = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(datetime.utcnow().strftime("%Y-%m-%d"))
    action: List[Action]

    class Config(BaseConfig):
        pass