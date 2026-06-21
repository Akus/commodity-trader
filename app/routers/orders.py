"""Order placement and lookup endpoints."""

from fastapi import APIRouter, HTTPException

from ..metrics import ORDER_NOTIONAL, ORDERS_TOTAL
from ..models import Order, OrderRequest, OrderStatus
from ..store import store

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=Order, status_code=201)
def place_order(req: OrderRequest) -> Order:
    order = store.place_order(req)
    ORDERS_TOTAL.labels(
        symbol=order.symbol, side=order.side.value, status=order.status.value
    ).inc()
    if order.status == OrderStatus.filled and order.notional is not None:
        ORDER_NOTIONAL.labels(symbol=order.symbol, side=order.side.value).observe(
            order.notional
        )
    return order


@router.get("", response_model=list[Order])
def list_orders() -> list[Order]:
    return store.list_orders()


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str) -> Order:
    order = store.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"unknown order '{order_id}'")
    return order
