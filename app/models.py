from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, JSON
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    sku = Column(String(50), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    available_stock = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("available_stock >= 0", name="check_stock_non_negative"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # CONFIRMED or REJECTED
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String(100), primary_key=True, index=True)
    status_code = Column(Integer, nullable=False)
    response_payload = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )