from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Brokers(Base):
    __tablename__ = "brokers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    machine_name = Column(String, unique=True)
    is_active = Column(Boolean, default=True)

class Symbols(Base):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    machine_name = Column(String, unique=True)
    type = Column(String) # Index, Equity
    option = Column(Boolean, default=True)
    lots = Column(Integer, default=0)
    strike_diff = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

class BrokerSymbols(Base):
    __tablename__ = "broker_symbols"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"))
    broker_id = Column(Integer, ForeignKey("brokers.id"))
    name = Column(String)

class Strategy(Base):
    __tablename__ = "strategy"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    machine_name = Column(String, unique=True)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow)
    exit_time = Column(DateTime, default=datetime.datetime.utcnow)
    is_paper = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

class Orderbook(Base):
    __tablename__ = "orderbook"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategy.id"))
    symbol = Column(String)
    ltp = Column(Integer, default=0)
    quantity = Column(Integer, default=0)
    status = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)