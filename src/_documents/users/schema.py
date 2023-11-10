import uuid
from datetime import datetime
from typing import Any, List
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

    class Config(BaseConfig):
        pass

class PaymentAccount(BaseModel):
    provider: str | None  # Paypal, Visacard, Mastercard, Bank
    bank_name: str | None
    account_name: str | None
    account_number: str | None
    paypal_email: EmailStr | None 

    class Config(BaseConfig):
        pass

class BillingInfo(BaseModel):
    name: str | None 
    address: str | None 
    country: str | None 
    tax_id: str | None 
    phone_number: str | None 
    email: EmailStr | None 

    class Config(BaseConfig):
        pass

class UserCreate(BaseModel):
    name: str | None 
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
    id: PyObjectId | None 
    name: str | None 
    display_name: str | None 
    gender: str | None 
    dob: str | None 
    address: str | None 
    phone_number: str | None 
    payment_accounts: List[PaymentAccount] | None 
    billing_info: BillingInfo | None 
    email_push_topics: List[str] | None 

    class Config(BaseConfig):
        pass


class UserList(UserUpdate):
    id: PyObjectId = Field(None, alias="_id")
    created_at: datetime | None 
    modified_at: datetime | None 
    roles: List[str] | None
    email: EmailStr | None 
    login_history: List[LoginHistory] | None 
    status: str | None 
    avatar_src: Any | None 
    email_push_topics: List[str] = Field(EMAIL_TOPICS)
    

class User(UserList):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    password: str | None 
    status: str = Field('pending')
    login_history: List[LoginHistory] = Field([])
    verify_token: str = Field(default_factory=lambda: uuid.uuid4().hex)


class UserAccess(UserList):
    access_role: str

