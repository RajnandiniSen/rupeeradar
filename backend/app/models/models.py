from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.core.db import Base
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Text

class ExchangeRate(Base):
    __tablename__ = "ex_rate"
    id: Mapped[int] = mapped_column(primary_key=True)
    rate: Mapped[float] = mapped_column()
    fetched_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))


class RateAlert(Base):
    __tablename__ = "rate_alert"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200))
    target_rate: Mapped[float] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

class Recommendation(Base):
    __tablename__ = "recommendation"
    id: Mapped[int] = mapped_column(primary_key=True)
    rate_snapshot_id: Mapped[int] = mapped_column(ForeignKey("ex_rate.id"))
    verdict: Mapped[str] = mapped_column(String(200))
    reasoning: Mapped[str] = mapped_column(Text)
    gen_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))