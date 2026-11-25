from fastapi import FastAPI, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BOPIS High-Throughput Order & Fulfillment Simulator",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/products", response_model=schemas.ProductResponse, status_code=201)
def create_or_reset_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(get_db),
):
    return crud.seed_product(db, product_in)


@app.get("/products/{sku}", response_model=schemas.ProductResponse)
def get_product(sku: str, db: Session = Depends(get_db)):
    product = db.get(models.Product, sku)
    if not product:
        return JSONResponse(status_code=404, content={"detail": "Product not found"})
    return product


@app.post("/orders", response_model=schemas.OrderResponse)
def place_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    status_code, payload = crud.process_order_with_lock(db, order_in, idempotency_key)
    return JSONResponse(status_code=status_code, content=payload)