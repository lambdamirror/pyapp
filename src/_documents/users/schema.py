import uuid
from datetime import datetime, timedelta
from typing import Any, List, Union
from _services.smtp.schema import EMAIL_TOPICS

from utils.schema import BaseConfig, ExtendedEnum, PyObjectId
from pydantic import BaseModel, EmailStr, Field


class Role(ExtendedEnum):
    DBA = 'database admin'

USER_STATUS = ['pending', 'active', 'inactive', 'locked', 'deleted']

USER_GENDER = ['Male', 'Female', 'Other']

BILLING_PROVIDER = ['Paypal', 'Visacard', 'Mastercard', 'Bank']


class LoginHistory(BaseModel):
    timestamp: List[datetime]
    ip_address: str
    user_agent: str


class PaymentAccount(BaseModel):
    provider: Union[None, str]  # Paypal, Visacard, Mastercard, Bank
    bank_name: Union[None, str]
    account_name: Union[None, str]
    account_number: Union[None, str]
    paypal_email: Union[None, EmailStr]


class BillingInfo(BaseModel):
    name: Union[None, str]
    address: Union[None, str]
    country: Union[None, str]
    tax_id: Union[None, str]
    phone_number: Union[None, str]
    email: Union[None, EmailStr]


class UserCreate(BaseModel):
    name: Union[None, str]
    email: EmailStr
    password: str
    confirm_password: str

    class Config(BaseConfig):
        scheme_extra = {
            "example": {
                "name": "Your Full Name",
                "email": "example@your_email.com",
                "password": "your_password",
                "confirm_password": "confirm_your_password"
            }
        }


class UserUpdate(BaseModel):
    id: Union[None, PyObjectId]
    name: Union[None, str]
    display_name: Union[None, str]
    gender: Union[None, str]
    dob: Union[None, str]
    address: Union[None, str]
    phone_number: Union[None, str]
    payment_accounts: Union[None, List[PaymentAccount]]
    billing_info: Union[None, BillingInfo]
    email_push_topics: Union[None, List[str]]

    class Config(BaseConfig):
        pass


class UserList(UserUpdate):
    id: PyObjectId = Field(None, alias="_id")
    created_at: Union[None, datetime]
    modified_at: Union[None, datetime]
    roles: List[str]
    email: Union[None, EmailStr]
    login_history: Union[None, List[LoginHistory]]
    status: Union[None, str]
    avatar_src: Union[None, Any]
    email_push_topics: List[str] = Field(EMAIL_TOPICS)


class User(UserList):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    password: Union[None, str]
    status: str = Field('pending')
    login_history: List[LoginHistory] = Field([])
    verify_token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    expired_time: Union[None, datetime]
