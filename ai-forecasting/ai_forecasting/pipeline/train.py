# Third Party
import joblib
import lightgbm as lgb
from sklearn.model_selection import train_test_split

from ..database import SessionLocal
from .features import generate_features

MODEL_PATH = "model.joblib"


def train_model():
    db = SessionLocal()
    try:
        df = generate_features(db)

        if df.empty or len(df) < 50:
            print("Not enough data to train model.")
            return False

        feature_cols = [
            "day_of_week",
            "is_weekend",
            "day_of_month",
            "volume_lag_1",
            "volume_lag_7",
            "volume_lag_14",
            "volume_lag_30",
            "volume_rolling_mean_7",
            "volume_rolling_std_7",
            "volume_rolling_mean_30",
            "price_rolling_mean_7",
            "price_trend",
            "is_ping",
            "is_doctrine",
        ]

        X = df[feature_cols]
        y = df["target_volume"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )

        model = lgb.LGBMRegressor(
            objective="tweedie", n_estimators=100, random_state=42
        )

        model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

        joblib.dump(model, MODEL_PATH)
        print(f"Model trained and saved to {MODEL_PATH}")
        return True
    finally:
        db.close()
