"""Commodity trading demo API entrypoint."""

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from . import __version__
from .routers import health, orders, quotes

app = FastAPI(
    title="Commodity Trading API",
    version=__version__,
    description="Demo commodity-trading API for the AKS/Flux home-lab.",
)

app.include_router(health.router)
app.include_router(quotes.router)
app.include_router(orders.router)


@app.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"service": "commodity-trading-api", "version": __version__}


# Exposes default HTTP metrics (request count/latency/in-flight) at /metrics,
# alongside the custom business metrics registered in app.metrics.
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
