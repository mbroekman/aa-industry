from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db, MarketTransaction, MarketPrice
from ..schemas import IngestPayload, ForecastRequest, ForecastResponse
from ..pipeline.train import train_model
from ..service.engine import calculate_forecast

router = APIRouter()

@router.post("/ingest")
def ingest_data(payload: IngestPayload, db: Session = Depends(get_db)):
    # Ingest Transactions
    for tx in payload.transactions:
        # Simplistic insert (in production we'd do bulk upsert)
        db_tx = MarketTransaction(
            date=tx.date,
            type_id=tx.type_id,
            volume_sold=tx.volume_sold,
            avg_price=tx.avg_price
        )
        db.add(db_tx)
        
    # Ingest Prices
    for p in payload.prices:
        db_price = db.query(MarketPrice).filter(MarketPrice.type_id == p.type_id).first()
        if db_price:
            db_price.price = p.price
        else:
            db_price = MarketPrice(type_id=p.type_id, price=p.price)
            db.add(db_price)
            
    db.commit()
    return {"status": "ok", "transactions_inserted": len(payload.transactions), "prices_updated": len(payload.prices)}

@router.post("/retrain")
def trigger_retrain(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_model)
    return {"status": "training_started"}

@router.post("/forecast", response_model=ForecastResponse)
def get_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    predicted_demand, rop, qty_to_build, conf = calculate_forecast(
        db, request.type_id, request.lead_time_days, request.safety_factor,
        request.current_stock, request.in_production
    )

    return ForecastResponse(
        type_id=request.type_id,
        predicted_daily_demand=predicted_demand,
        qty_to_build=qty_to_build,
        confidence_score=conf,
        reorder_point=rop
    )
