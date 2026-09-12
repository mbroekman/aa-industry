# Standard Library

# Third Party
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Float,
    Integer,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

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


class PingEvent(Base):
    __tablename__ = "ping_events"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    is_ping = Column(Integer, default=1)


class DoctrineEvent(Base):
    __tablename__ = "doctrine_events"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    type_id = Column(BigInteger, index=True)
    is_doctrine = Column(Integer, default=1)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
