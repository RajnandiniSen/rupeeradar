import httpx
from datetime import datetime, timezone
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


async def backfill_rates(db, start_date, end_date):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.frankfurter.dev/v1/{start_date}..{end_date}?from=USD&to=INR")
    data = response.json()
    for date, rates in data["rates"].items():
        rate = rates["INR"]
        fetched_at = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        record = ExchangeRate(rate=rate, fetched_at=fetched_at)
        db.add(record)
    db.commit()
    return {"backfilled": len(data["rates"])}
