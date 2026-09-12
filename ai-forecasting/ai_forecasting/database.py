from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./data.sqlite3"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MarketTransaction(Base):
    __tablename__ = "market_transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    type_id = Column(BigInteger, index=True)
    volume_sold = Column(Float)
    avg_price = Column(Float)

class MarketPrice(Base):
    __tablename__ = "market_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    type_id = Column(BigInteger, index=True, unique=True)
    price = Column(Float)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
