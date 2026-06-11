from fastapi import FastAPI
from app.core.db import engine, Base
from app.models.models import ExchangeRate, RateAlert, Recommendation

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_status():
    return {"status" : "ok"}

