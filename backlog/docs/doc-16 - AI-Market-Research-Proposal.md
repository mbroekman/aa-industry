---
id: doc-16
title: 'AI Market Research Proposal'
type: guide
created_date: '2026-09-12 13:26'
updated_date: '2026-09-12 13:46'
---

# Proposal: AI Market Demand Forecasting & Order Trigger Service

This proposal outlines the architecture and approach for implementing a predictive market demand model based on LightGBM and FastAPI, running as a separate service that integrates with `aa-industry`.

## 1. Objective

The objective is to utilize historical sales data combined with external factors to predict the daily consumption (`daily_volume`) of items. Based on these predictions, a deterministic engine calculates the Reorder Point (ROP) and automatically triggers production tasks (build orders).

The Machine Learning model strictly predicts demand (quantities). Hard business rules in the trigger engine determine the exact build quantities.

## 2. Architecture & Integration

The application will be built as an **isolated FastAPI Microservice** and deployed as a separate Docker image alongside the existing Alliance Auth stack.

**Communication Flow:**
*   **Data Ingestion:** The main application (Alliance Auth) periodically pushes historical transaction data, external variables, and configurations to the microservice via an HTTP API.
*   **Forecasting:** Auth requests current predictions and ROP values via a `/forecast` endpoint during basket evaluation.

This guarantees that the memory and CPU overhead of the LightGBM model will not impact the main application.

## 3. Components & Deliverables

The codebase will focus on strict typing, a low memory footprint (CPU-only), and seamless API integration.

### 3.1 `pipeline/features.py` (Data & Feature Engineering)
Responsible for transforming raw data into training-ready datasets.
*   **Historical Aggregation**: Grouping by `date` and `type_id`.
*   **Time-series Features**: Lag features (1, 7, 14 days) and rolling statistics (mean, std).
*   **Calendar**: Day of the week, weekend indicators.
*   **Context & External Signals**:
    *   **Alliance Pings & Doctrine Shifts**: Indicators driving spikes in demand.
    *   **Market Prices**: Changing market prices and trends.
*   **Data Splitting**: Time-series split to prevent *data leakage*.

### 3.2 `pipeline/train.py` (Model Training)
*   **Algorithm**: `LGBMRegressor` (LightGBM).
*   **Objective**: `poisson` or `tweedie`.
*   **Output**: Saving the trained model as an artifact.

### 3.3 `service/engine.py` (Deterministic Trigger Engine)
The bridge between prediction and action.
*   **Lead Time**: `Production Lead Time = (Exact Blueprint Build Time * Modifiers) + Adjustable Margin`. (The margin accounts for the time required by players to claim a task).
*   **Formula**: `ROP = (Forecasted Daily Demand * Production Lead Time) + Safety Stock`.
*   **Logic**: `IF (Current Stock + In_Production) < ROP THEN Build_Qty = (Target Stock - Current Stock - In_Production)`.

### 3.4 `api/routes.py` (FastAPI Endpoints)
*   `POST /ingest`: Receives historical dataset payloads (transactions, pings, market prices) from Auth.
*   `POST /retrain`: Triggers model training on the latest data.
*   `POST /forecast`: Returns ROP and build quantities based on provided parameters and the current forecast.

### 3.5 Opportunity Scanner Integration
The existing Opportunity Scanner will be enhanced to utilize the AI service:
*   Instead of relying on naive `velocity` metrics, the scanner will query the `/forecast` endpoint for new items.
*   If the AI model predicts a sustained high demand (despite external factors), the opportunity will be marked as "High Confidence", providing Directors with more reliable market discovery insights.

## 4. Implementation Steps

1.  **Project & Docker Setup**: Initialize the new codebase (Poetry) and setup the Docker image for FastAPI.
2.  **API Data Ingestion**: Setup schemas (Pydantic) and endpoints to receive and store data from Alliance Auth.
3.  **Pipeline Engineering**: Implement `features.py` (including external context features) and `train.py` with test datasets.
4.  **Engine Development**: Implement ROP calculations using blueprint build times and flexible margins.
5.  **Integration in `aa-industry`**:
    *   Write an Auth Celery task to periodically push data to `/ingest` and trigger `/retrain`.
    *   Adapt the `evaluate_baskets` module to call `/forecast` instead of using static target levels.
    *   Update the Opportunity Scanner logic to query the AI model for forecasted demand instead of using naive velocity, and display confidence metrics in the scanner UI.
