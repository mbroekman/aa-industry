import pandas as pd
from sqlalchemy.orm import Session
from ..database import MarketTransaction

def generate_features(db: Session, target_horizon: int = 7) -> pd.DataFrame:
    query = db.query(MarketTransaction).statement
    df = pd.read_sql(query, db.bind)
    
    if df.empty:
        return pd.DataFrame()
        
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['type_id', 'date'])
    
    # Calendar features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['day_of_month'] = df['date'].dt.day
    
    features = []
    
    for type_id, group in df.groupby('type_id'):
        group = group.set_index('date').resample('D').sum().reset_index()
        group['type_id'] = type_id
        
        # Lag features
        group['volume_lag_1'] = group['volume_sold'].shift(1)
        group['volume_lag_7'] = group['volume_sold'].shift(7)
        group['volume_lag_14'] = group['volume_sold'].shift(14)
        group['volume_lag_30'] = group['volume_sold'].shift(30)
        
        # Rolling stats (based on past data, so we shift 1 before rolling)
        past_vol = group['volume_sold'].shift(1)
        group['volume_rolling_mean_7'] = past_vol.rolling(window=7, min_periods=1).mean()
        group['volume_rolling_std_7'] = past_vol.rolling(window=7, min_periods=1).std()
        group['volume_rolling_mean_30'] = past_vol.rolling(window=30, min_periods=1).mean()
        
        # Target: sum of volume over the next `target_horizon` days
        # Shift back by target_horizon to align future demand with today's features
        group['target_volume'] = group['volume_sold'].shift(-target_horizon).rolling(window=target_horizon).sum()
        
        features.append(group)
        
    if not features:
        return pd.DataFrame()
        
    full_df = pd.concat(features, ignore_index=True)
    return full_df.dropna() # Drop rows where lag or target is NaN
