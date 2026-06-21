"""Pydantic models for the commodity trading API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Side(str, Enum):
    buy = "buy"
    sell = "sell"


class OrderStatus(str, Enum):
    filled = "filled"
    rejected = "rejected"


class Quote(BaseModel):
    symbol: str = Field(..., examples=["GOLD"])
    name: str = Field(..., examples=["Gold (troy oz)"])
    currency: str = Field(default="USD")
    price: float = Field(..., examples=[2345.12])
    as_of: datetime


class OrderRequest(BaseModel):
    symbol: str = Field(..., examples=["GOLD"])
    side: Side = Field(..., examples=["buy"])
    quantity: float = Field(..., gt=0, examples=[10])
    limit_price: float | None = Field(
        default=None,
        gt=0,
        description="If set, a buy fills only at/below it and a sell at/above it.",
    )


class Order(BaseModel):
    id: str
    symbol: str
    side: Side
    quantity: float
    status: OrderStatus
    filled_price: float | None
    notional: float | None
    reason: str | None = None
    created_at: datetime
