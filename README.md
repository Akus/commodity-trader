# Commodity Trading API

FastAPI demo service for the AKS/Flux home-lab. Provides commodity quotes and a
simple order endpoint, plus Prometheus metrics for observability and load tests.

> **Deployment:** this repo only builds and pushes the container image to ACR
> (`akoscommodityacr.azurecr.io/commodity-api`). The cluster/infra lives in the
> `AKS` repo (Terraform) and the runtime manifests in the Flux repo
> (`flux-simple-kubernetes-cluster`); CI here promotes the image across
> dev → preprod → prod by bumping the Flux overlays. See `azure-pipelines/`.

## Endpoints

| Method | Path             | Description                                  |
|--------|------------------|----------------------------------------------|
| GET    | `/`              | Service/version info                         |
| GET    | `/healthz`       | Liveness probe                               |
| GET    | `/readyz`        | Readiness probe                              |
| GET    | `/quotes`        | All commodity quotes (prices random-walk)    |
| GET    | `/quotes/{sym}`  | Single quote (404 if unknown)                |
| POST   | `/orders`        | Place an order (market or limit)             |
| GET    | `/orders`        | List placed orders                           |
| GET    | `/orders/{id}`   | Look up an order                             |
| GET    | `/metrics`       | Prometheus metrics                           |
| GET    | `/docs`          | OpenAPI / Swagger UI                         |

Symbols: `GOLD SILVER WTI BRENT NATGAS COPPER WHEAT CORN`.

Custom metrics: `commodity_orders_total{symbol,side,status}` and
`commodity_order_notional_usd{symbol,side}` (histogram), alongside the default
HTTP request count/latency/in-flight series.

## Run locally

```bash
python -m venv .venv && . .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080
# http://localhost:8080/docs
```

## Test & lint

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

## Build & run with Podman

```bash
podman build -t commodity-api:dev .
podman run --rm -p 8080:8080 commodity-api:dev
curl localhost:8080/quotes/GOLD
```

Example order:

```bash
curl -X POST localhost:8080/orders \
  -H 'content-type: application/json' \
  -d '{"symbol":"GOLD","side":"buy","quantity":10}'
```
