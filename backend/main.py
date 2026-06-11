from fastapi import FastAPI
from app.api.rates import router as rates_router
from app.core.db import engine, Base
from app.models.models import ExchangeRate, RateAlert, Recommendation

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rates_router)

@app.get("/health")
def health_status():
    return {"status" : "ok"}
