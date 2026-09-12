# AI Demand Forecasting Service

FastAPI service for predicting demand and triggering manufacturing orders using LightGBM.

## Prerequisites

- **Podman** (Recommended)
- **Poetry** (If running locally without Podman)
- Python 3.11+

## Installation & Running (Podman)

The easiest way to run the service is using Podman.

1. Build the Podman image:
   ```bash
   podman build -t ai-forecasting .
   ```
2. Run the Podman container (runs on port 8050):
   ```bash
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

Once the service is running on `http://127.0.0.1:8050`, the Alliance Auth `aa-industry` app will automatically start communicating with it via background Celery tasks.

- **Ingestion (`/ingest`)**: The `sync_market_data_to_ml_service` Celery task pushes transaction data here.
- **Training (`/retrain`)**: Triggers the LightGBM model training on historical data.
- **Forecasting (`/forecast`)**: The Opportunity Scanner and Basket Evaluation modules query this endpoint for real-time demand and Reorder Point (ROP) calculations.
