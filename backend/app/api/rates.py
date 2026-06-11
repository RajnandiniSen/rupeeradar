from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.forex import backfill_rates, fetch_and_store_rate

router = APIRouter(prefix="/api/rates")


@router.post("/refresh")
async def refresh_rate(db: Session = Depends(get_db)):
    return await fetch_and_store_rate(db)

@router.post("/backfill")
async def backfill(start_date: str, end_date: str, db: Session = Depends(get_db)):
    return await backfill_rates(db, start_date, end_date)
