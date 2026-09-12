Implement a lightweight demand forecasting and automated manufacturing order trigger service using Python, LightGBM, and FastAPI to integrate with our industry tool.

### Objective
Predict daily consumption (`daily_volume`) for market items at a specific structure over a dynamic forecast horizon (e.g., 7–14 days), calculate the Reorder Point (ROP), and issue build orders when inventory levels fall below safety thresholds.

### Architectural Requirements
1. **Module / Service**: Create an isolated microservice (or internal worker package) with two modes:
   - **Training Pipeline**: CLI / scheduled task to fit a LightGBM regressor per item or per category using tabular historical transaction data.
   - **Inference API**: A lightweight FastAPI endpoint (or background job) returning predicted demand and manufacturing recommendations.
2. **Deterministic Trigger Engine**:
   - Calculate `Reorder Point (ROP) = (Forecasted Daily Demand * Production Lead Time in Days) + Safety Stock`.
   - Condition: If `(Current Stock + Stock Under Construction) < ROP`, generate a build order with `Order Quantity = (Target Stock Level - Current Stock - Stock Under Construction)`.
   - Never let the ML model directly output binary build decisions; ML predicts demand quantities, business logic triggers orders.

### Feature Engineering (LightGBM)
Input: Time-series transaction history aggregated by date and `type_id` (`date`, `type_id`, `volume_sold`, `avg_price`).
Required features:
- **Lag features**: `volume_lag_1`, `volume_lag_7`, `volume_lag_14`, `volume_lag_30`.
- **Rolling statistics**: `volume_rolling_mean_7`, `volume_rolling_std_7`, `volume_rolling_mean_30`.
- **Calendar features**: `day_of_week`, `is_weekend`, `day_of_month`.
- **Target**: `target_volume_next_n_days` (or recursive 1-day step).

### Deliverables
1. **`pipeline/features.py`**: Data preprocessing, feature engineering (lags, rolling windows), and train/test split (time-series split, no future leakage).
2. **`pipeline/train.py`**: LightGBM model training using `LGBMRegressor` (objective: `poisson` or `tweedie` for zero-inflated demand, or `regression_l1`), saving model artifacts locally via `joblib`.
3. **`service/engine.py`**: Business logic calculating ROP, safety stock, and evaluating inventory status to emit structured build order payloads.
4. **`api/routes.py`**:
   - `POST /forecast`: Accepts `{ type_id, current_stock, in_production, lead_time_days, safety_factor }`, returns predicted daily demand and recommended build quantity (`qty_to_build`).
   - `POST /retrain`: Triggers pipeline execution on the latest market transaction dataset.
5. **Tests**: Unit tests for ROP calculation and feature lag creation with dummy market data.

Keep the codebase strictly typed, minimal, and container-ready with low memory overhead (CPU-only LightGBM).