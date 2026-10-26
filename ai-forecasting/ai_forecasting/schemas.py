# Standard Library
import datetime

# Third Party
from pydantic import BaseModel


class TransactionIngest(BaseModel):
    date: datetime.date
    type_id: int
    volume_sold: float
    avg_price: float


class PriceIngest(BaseModel):
    type_id: int
    price: float


class PingIngest(BaseModel):
    date: datetime.date
    is_ping: int = 1


class DoctrineIngest(BaseModel):
    date: datetime.date
    type_id: int
    is_doctrine: int = 1


class IngestPayload(BaseModel):
    transactions: list[TransactionIngest] = []
    prices: list[PriceIngest] = []
    pings: list[PingIngest] = []
    doctrines: list[DoctrineIngest] = []


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
