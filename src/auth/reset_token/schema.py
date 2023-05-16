from typing import Any
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from utils.schema import BaseConfig, PyObjectId

class ResetToken(BaseModel):
    user_id: PyObjectId
    token: str = Field(default_factory=lambda : uuid.uuid4().hex)
    type: str # password, email
    data: Any
    status: bool
    expired_time: datetime

    class Config(BaseConfig):
        pass


class ResetPassword(BaseModel):
    password: str
    confirm_password: str


