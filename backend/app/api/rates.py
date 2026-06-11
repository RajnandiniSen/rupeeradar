from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import ExchangeRate
from app.services.forex import backfill_rates, fetch_and_store_rate
from app.services.llm import get_recommendation

from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/rates")


@router.post("/refresh")
async def refresh_rate(db: Session = Depends(get_db)):
    return await fetch_and_store_rate(db)

@router.post("/backfill")
async def backfill(start_date: str, end_date: str, db: Session = Depends(get_db)):
    return await backfill_rates(db, start_date, end_date)


@router.get("/history")
def rate_history(days: int = 30, db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.query(ExchangeRate)
        .filter(ExchangeRate.fetched_at >= cutoff)
        .order_by(ExchangeRate.fetched_at.asc())
        .all()
    )


@router.get("/recommend")
def recommend_rate(db: Session = Depends(get_db)):
    latest_rate = (
        db.query(ExchangeRate)
        .order_by(ExchangeRate.fetched_at.desc())
        .first()
    )

    if latest_rate is None:
        raise HTTPException(status_code=404, detail="No exchange rates found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    stats = (
        db.query(
            func.max(ExchangeRate.rate),
            func.min(ExchangeRate.rate),
            func.avg(ExchangeRate.rate),
        )
        .filter(ExchangeRate.fetched_at >= cutoff)
        .first()
    )
    high_30d, low_30d, avg_30d = stats

    if high_30d is None or low_30d is None or avg_30d is None:
        raise HTTPException(status_code=404, detail="No exchange rates found in the last 30 days")

    return get_recommendation(latest_rate.rate, high_30d, low_30d, avg_30d)
