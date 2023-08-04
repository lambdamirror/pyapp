
from typing import Callable, Dict, List, Union
from pydantic import BaseModel, Field, validator


class OrderBillingData(BaseModel):
    qty: int = Field(0)
    base: float = Field(0)
    ratio: float = Field(0)
    billing_ref: Union[None, str]
    billing_paid: bool = Field(False)


class DashboardConfig(BaseModel):
    role: str
    allowed_docs: Union[None, List[str]]
    allowed_options: Dict[str, List[str]] = Field({})
    query: Dict[str, dict]


class StorageConfig(BaseModel):
    role: str
    order_query: Union[Callable, dict] = Field({ 'status': {'$ne': 'DELETED'}})
    show_payment: bool = Field(False)
    allowed_options: Union[None, Dict[str, List[str]]]


class RecordsConfig(BaseModel):
    role: str
    order_query:  Union[Callable, dict] = Field({ 'status': {'$ne': 'DELETED'}})
    allowed_fns: List[str] = Field([])