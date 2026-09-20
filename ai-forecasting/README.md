# AI Demand Forecasting Service

FastAPI service for predicting demand and triggering manufacturing orders using LightGBM.

## Prerequisites

- **Podman** (Recommended)
- **Poetry** (If running locally without Podman)
- Python 3.11+

## Installation & Running (Podman)

The easiest way to run the service is using the pre-built Podman image from the GitHub Container Registry.

```bash
podman run -d -p 8050:8050 --name ai-forecasting ghcr.io/mbroekman/aa-industry-ai-forecasting:latest
```

If you wish to build the image manually:
```bash
podman build -t ai-forecasting .
podman run -p 8050:8050 ai-forecasting
```

## Local Development (Poetry)

If you prefer to run the service locally without Podman:

1. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
2. Start the FastAPI server:
   ```bash
   poetry run uvicorn ai_forecasting.main:app --host 0.0.0.0 --port 8050 --reload
   ```

## Integration with aa-industry

Once the service is running, you must configure the Alliance Auth `aa-industry` app to point to it by adding the following setting to your `local.py`:

```python
INDUSTRY_REFORGED_AI_URL = "http://127.0.0.1:8050" 
# NOTE: If you are running Alliance Auth in a container (e.g. Podman/Docker) and Uvicorn on the host, 
# use "http://host.containers.internal:8050" instead.
```

If this setting is omitted, it defaults to `http://127.0.0.1:8050`. Once configured, the background Celery tasks will automatically start communicating with the service:

- **Ingestion (`/ingest`)**: The `sync_market_data_to_ml_service` Celery task pushes transaction data here.
- **Training (`/retrain`)**: Triggers the LightGBM model training on historical data.
- **Forecasting (`/forecast`)**: The Opportunity Scanner and Basket Evaluation modules query this endpoint for real-time demand and Reorder Point (ROP) calculations.
