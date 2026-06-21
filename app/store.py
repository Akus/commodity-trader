"""In-memory market data + order book.

Prices random-walk on each read so /quotes and load tests produce varied,
metric-worthy traffic without any external dependency.
"""

from __future__ import annotations

import random
import threading
import uuid
from datetime import UTC, datetime

from .models import Order, OrderRequest, OrderStatus, Quote, Side

# symbol -> (display name, seed price)
_SEED: dict[str, tuple[str, float]] = {
    "GOLD": ("Gold (troy oz)", 2345.0),
    "SILVER": ("Silver (troy oz)", 29.4),
    "WTI": ("Crude Oil WTI (bbl)", 78.2),
    "BRENT": ("Crude Oil Brent (bbl)", 82.6),
    "NATGAS": ("Natural Gas (MMBtu)", 2.85),
    "COPPER": ("Copper (lb)", 4.55),
    "WHEAT": ("Wheat (bushel)", 5.92),
    "CORN": ("Corn (bushel)", 4.41),
}


class MarketStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._prices: dict[str, float] = {s: p for s, (_, p) in _SEED.items()}
        self._orders: dict[str, Order] = {}

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _tick(self, symbol: str) -> float:
        """Apply a small random walk (±0.25%) and return the new price."""
        price = self._prices[symbol]
        price *= 1 + random.uniform(-0.0025, 0.0025)
        price = round(price, 4)
        self._prices[symbol] = price
        return price

    def list_quotes(self) -> list[Quote]:
        with self._lock:
            now = self._now()
            return [
                Quote(
                    symbol=s,
                    name=_SEED[s][0],
                    price=self._tick(s),
                    as_of=now,
                )
                for s in _SEED
            ]

    def get_quote(self, symbol: str) -> Quote | None:
        symbol = symbol.upper()
        if symbol not in _SEED:
            return None
        with self._lock:
            return Quote(
                symbol=symbol,
                name=_SEED[symbol][0],
                price=self._tick(symbol),
                as_of=self._now(),
            )

    def place_order(self, req: OrderRequest) -> Order:
        symbol = req.symbol.upper()
        with self._lock:
            if symbol not in _SEED:
                return self._reject(req, f"unknown symbol '{req.symbol}'")

            market = self._tick(symbol)
            if req.limit_price is not None:
                crossed = (
                    req.side == Side.buy and market <= req.limit_price
                ) or (req.side == Side.sell and market >= req.limit_price)
                if not crossed:
                    return self._reject(
                        req, f"limit {req.limit_price} not crossed (market {market})"
                    )

            order = Order(
                id=uuid.uuid4().hex,
                symbol=symbol,
                side=req.side,
                quantity=req.quantity,
                status=OrderStatus.filled,
                filled_price=market,
                notional=round(market * req.quantity, 2),
                created_at=self._now(),
            )
            self._orders[order.id] = order
            return order

    def _reject(self, req: OrderRequest, reason: str) -> Order:
        return Order(
            id=uuid.uuid4().hex,
            symbol=req.symbol.upper(),
            side=req.side,
            quantity=req.quantity,
            status=OrderStatus.rejected,
            filled_price=None,
            notional=None,
            reason=reason,
            created_at=self._now(),
        )

    def list_orders(self) -> list[Order]:
        with self._lock:
            return list(self._orders.values())

    def get_order(self, order_id: str) -> Order | None:
        with self._lock:
            return self._orders.get(order_id)


store = MarketStore()
