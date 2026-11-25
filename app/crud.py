from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models, schemas


def seed_product(db: Session, product_in: schemas.ProductCreate) -> models.Product:
    existing = db.get(models.Product, product_in.sku)
    if existing:
        existing.name = product_in.name
        existing.available_stock = product_in.available_stock
        db.commit()
        db.refresh(existing)
        return existing

    product = models.Product(
        sku=product_in.sku,
        name=product_in.name,
        available_stock=product_in.available_stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def process_order_with_lock(
    db: Session,
    order_in: schemas.OrderCreate,
    idempotency_key: str | None = None,
) -> tuple[int, dict]:
    if idempotency_key:
        cached = db.get(models.IdempotencyRecord, idempotency_key)
        if cached:
            return cached.status_code, cached.response_payload

    stmt = (
        select(models.Product)
        .where(models.Product.sku == order_in.sku)
        .with_for_update()
    )
    product = db.execute(stmt).scalar_one_or_none()

    if not product:
        payload = {"detail": f"SKU '{order_in.sku}' not found"}
        status_code = 404
    elif product.available_stock < order_in.quantity:
        rejected_order = models.Order(
            sku=order_in.sku,
            quantity=order_in.quantity,
            status="REJECTED",
        )
        db.add(rejected_order)
        payload = {
            "detail": "Insufficient inventory",
            "sku": product.sku,
            "requested": order_in.quantity,
            "available_stock": product.available_stock,
        }
        status_code = 409
    else:
        product.available_stock -= order_in.quantity
        confirmed_order = models.Order(
            sku=order_in.sku,
            quantity=order_in.quantity,
            status="CONFIRMED",
        )
        db.add(confirmed_order)
        db.flush()

        payload = {
            "order_id": confirmed_order.id,
            "sku": confirmed_order.sku,
            "quantity": confirmed_order.quantity,
            "status": confirmed_order.status,
            "remaining_stock": product.available_stock,
            "created_at": confirmed_order.created_at.isoformat(),
        }
        status_code = 201

    if idempotency_key:
        record = models.IdempotencyRecord(
            key=idempotency_key,
            status_code=status_code,
            response_payload=payload,
        )
        db.add(record)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            cached = db.get(models.IdempotencyRecord, idempotency_key)
            if cached:
                return cached.status_code, cached.response_payload
        return 409, {"detail": "Concurrent transaction conflict"}

    return status_code, payload