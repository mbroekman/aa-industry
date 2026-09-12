# Third Party
import pandas as pd
from sqlalchemy.orm import Session

from ..database import DoctrineEvent, MarketTransaction, PingEvent


def generate_features(db: Session, target_horizon: int = 7) -> pd.DataFrame:
    query = db.query(MarketTransaction).statement
    df = pd.read_sql(query, db.bind)

    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["type_id", "date"])

    # Load pings
    pings_query = db.query(PingEvent).statement
    pings_df = pd.read_sql(pings_query, db.bind)
    if not pings_df.empty:
        pings_df["date"] = pd.to_datetime(pings_df["date"])
        pings_df = pings_df.groupby("date")["is_ping"].max().reset_index()
    else:
        pings_df = pd.DataFrame(columns=["date", "is_ping"])

    # Load doctrines
    doc_query = db.query(DoctrineEvent).statement
    doc_df = pd.read_sql(doc_query, db.bind)
    if not doc_df.empty:
        doc_df["date"] = pd.to_datetime(doc_df["date"])
        doc_df = doc_df.groupby(["date", "type_id"])["is_doctrine"].max().reset_index()
    else:
        doc_df = pd.DataFrame(columns=["date", "type_id", "is_doctrine"])

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["day_of_month"] = df["date"].dt.day

    features = []

    for type_id, group in df.groupby("type_id"):
        group = (
            group.set_index("date")
            .resample("D")
            .agg(
                {
                    "volume_sold": "sum",
                    "avg_price": "mean",
                    "day_of_week": "first",
                    "is_weekend": "first",
                    "day_of_month": "first",
                }
            )
            .reset_index()
        )

        # Merge pings
        group = pd.merge(group, pings_df, on="date", how="left")
        group["is_ping"] = group["is_ping"].fillna(0).astype(int)

        # Merge doctrines
        type_docs = doc_df[doc_df["type_id"] == type_id]
        if not type_docs.empty:
            group = pd.merge(
                group, type_docs[["date", "is_doctrine"]], on="date", how="left"
            )
            group["is_doctrine"] = group["is_doctrine"].fillna(0).astype(int)
        else:
            group["is_doctrine"] = 0

        group["type_id"] = type_id

        # Lag features
        group["volume_lag_1"] = group["volume_sold"].shift(1)
        group["volume_lag_7"] = group["volume_sold"].shift(7)
        group["volume_lag_14"] = group["volume_sold"].shift(14)
        group["volume_lag_30"] = group["volume_sold"].shift(30)

        # Rolling stats (based on past data, so we shift 1 before rolling)
        past_vol = group["volume_sold"].shift(1)
        group["volume_rolling_mean_7"] = past_vol.rolling(
            window=7, min_periods=1
        ).mean()
        group["volume_rolling_std_7"] = past_vol.rolling(window=7, min_periods=1).std()
        group["volume_rolling_mean_30"] = past_vol.rolling(
            window=30, min_periods=1
        ).mean()

        # Price features
        group["price_rolling_mean_7"] = (
            group["avg_price"].shift(1).rolling(window=7, min_periods=1).mean()
        )
        group["price_trend"] = (
            group["avg_price"].shift(1) / group["price_rolling_mean_7"]
        )
        group["price_trend"] = group["price_trend"].fillna(1.0)
        group["price_rolling_mean_7"] = group["price_rolling_mean_7"].fillna(
            method="bfill"
        )

        # Target: sum of volume over the next `target_horizon` days
        # Shift back by target_horizon to align future demand with today's features
        group["target_volume"] = (
            group["volume_sold"]
            .shift(-target_horizon)
            .rolling(window=target_horizon)
            .sum()
        )

        features.append(group)

    if not features:
        return pd.DataFrame()

    full_df = pd.concat(features, ignore_index=True)
    return full_df.dropna()  # Drop rows where lag or target is NaN
