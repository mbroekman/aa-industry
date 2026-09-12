import joblib
import pandas as pd
from sqlalchemy.orm import Session
from ..pipeline.train import MODEL_PATH
from ..pipeline.features import generate_features

# Cache model
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            return None
    return _model

def calculate_forecast(db: Session, type_id: int, lead_time_days: int, safety_factor: float, current_stock: int, in_production: int):
    model = get_model()
    
    predicted_daily_demand = 0.0
    confidence = 0.5
    
    if model:
        # Get latest features for this type_id
        df = generate_features(db)
        if not df.empty:
            type_df = df[df['type_id'] == type_id]
            if not type_df.empty:
                latest_features = type_df.iloc[-1:]
                feature_cols = [
                    'day_of_week', 'is_weekend', 'day_of_month',
                    'volume_lag_1', 'volume_lag_7', 'volume_lag_14', 'volume_lag_30',
                    'volume_rolling_mean_7', 'volume_rolling_std_7', 'volume_rolling_mean_30'
                ]
                X = latest_features[feature_cols]
                # model predicts total over next horizon (e.g. 7 days)
                predicted_total = model.predict(X)[0]
                predicted_daily_demand = max(0.0, predicted_total / 7.0)
                confidence = 0.85
                
    rop = (predicted_daily_demand * lead_time_days) + (predicted_daily_demand * safety_factor)
    current_total = current_stock + in_production
    qty_to_build = int(rop - current_total) if current_total < rop else 0

    return predicted_daily_demand, rop, qty_to_build, confidence
