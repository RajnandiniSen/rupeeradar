from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_engine("postgresql://rupeeradar:rupeeradar123@localhost:5432/rupeeradar")
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
class Base(DeclarativeBase):
    pass
