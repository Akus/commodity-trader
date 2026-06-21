"""Custom business metrics, exposed alongside the default HTTP metrics."""

from prometheus_client import Counter, Histogram

ORDERS_TOTAL = Counter(
    "commodity_orders_total",
    "Orders processed, labelled by symbol, side and outcome.",
    ["symbol", "side", "status"],
)

ORDER_NOTIONAL = Histogram(
    "commodity_order_notional_usd",
    "Notional value (USD) of filled orders.",
    ["symbol", "side"],
    buckets=(100, 1_000, 10_000, 50_000, 100_000, 500_000, 1_000_000),
)
