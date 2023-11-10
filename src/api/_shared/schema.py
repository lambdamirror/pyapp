
from typing import Callable, Dict, List
from pydantic import BaseModel, Field, validator


class OrderBillingData(BaseModel):
    qty: int = Field(0)
    base: float = Field(0)
    ratio: float = Field(0)
    billing_ref: str | None
    billing_paid: bool = Field(False)


class DashboardConfig(BaseModel):
    role: str
    allowed_docs: List[str] | None
    allowed_options: Dict[str, List[str]] = Field({})
    query: Dict[str, dict]


class StorageConfig(BaseModel):
    role: str
    order_query: Callable | dict = Field({ 'status': {'$ne': 'DELETED'}})
    show_payment: bool = Field(False)
    allowed_options: Dict[str, List[str]] | None


class RecordsConfig(BaseModel):
    role: str
    order_query:  Callable | dict = Field({ 'status': {'$ne': 'DELETED'}})
    allowed_fns: List[str] = Field([])