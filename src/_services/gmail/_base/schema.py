from typing import List, Union

from utils.schema import BaseConfig, PyObjectId
from pydantic import BaseModel, Field


class GmailBaseConfig(BaseModel):
    user_id: str
    history_id: str = Field('')
    scopes: List[str] = Field([
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.settings.basic'
    ])
    service_account_file: str 
    project_id: str
    topic_id: str
    subscription_id: str

    class Config(BaseConfig):
        pass

class MessageStatus(BaseModel):
    count: int = Field(0)
    history_id: str = Field('')

    class Config(BaseConfig):
        pass