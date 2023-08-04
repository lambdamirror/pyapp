from typing import List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Union

from _documents.users.schema import Role
from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field

CONTENT_TYPE = [
    'order_create', 'order_update', 'order_status'
]


class UserStatus(BaseModel):
    user_id: PyObjectId
    status: str = 'UNREAD'


class NotificationCreate(BaseModel):
    sender: PyObjectId
    users: List[UserStatus]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    document: str
    content_type: str # order_create order_update order_deliver order_cancel
    reference_id: PyObjectId
    title: str
    message: str
    image_url: Union[None, str]
    view_url: Union[None, str]


class NotificationList(NotificationCreate):
    id: PyObjectId = Field(None, alias='_id')
    users: List[UserStatus] = Field([])
    user: Union[None, PyObjectId]
    sender: Union[None, PyObjectId]
    status: Union[None, str]

    class Config(BaseConfig):
        pass


class Notification(NotificationCreate):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)

    class Config(BaseConfig):
        pass