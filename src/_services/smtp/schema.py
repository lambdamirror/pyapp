from typing import List
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

EMAIL_TOPICS = [
    "order_create", "order_status_update",
    "request_add", "request_update", "request_finish", "request_cancel",
    "request_comment_add", "request_comment_modify",
    "billing", "transaction"
]


class EmailSchema(BaseModel):
    subject: str
    recipients: List[EmailStr] = Field([])
    cc: List[EmailStr] = Field([])
    body: str | None
