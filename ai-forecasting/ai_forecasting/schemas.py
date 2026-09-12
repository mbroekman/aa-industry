from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class TransactionIngest(BaseModel):
    date: date
    type_id: int
    volume_sold: float
    avg_price: float

class PriceIngest(BaseModel):
    type_id: int
    price: float

class IngestPayload(BaseModel):
    transactions: List[TransactionIngest] = []
    prices: List[PriceIngest] = []

class ForecastRequest(BaseModel):
    type_id: int
    current_stock: int
    in_production: int
    lead_time_days: int
    safety_factor: float

class ForecastResponse(BaseModel):
    type_id: int
    predicted_daily_demand: float
    qty_to_build: int
    confidence_score: float
    reorder_point: float
