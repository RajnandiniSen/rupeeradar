import httpx
from sqlalchemy.orm import Session
from app.models.models import ExchangeRate

async def fetch_current_rate():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.frankfurter.dev/v1/latest?from=USD&to=INR")
    return response.json()["rates"]["INR"]

async def fetch_and_store_rate(db: Session):
    rate = await fetch_current_rate()
    record = ExchangeRate(rate=rate)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record