from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.db import SessionLocal
from app.services.forex import fetch_and_store_rate


async def refresh_rate_job():
    db = SessionLocal()
    try:
        await fetch_and_store_rate(db)
    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_rate_job, "interval", minutes=60)
    scheduler.start()
    return scheduler
