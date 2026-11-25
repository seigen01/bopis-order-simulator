# BOPIS High-Throughput Order & Fulfillment Event Simulator

A containerized backend service built with **Python**, **FastAPI**, **SQLAlchemy**, and **PostgreSQL 16** that prevents inventory overselling and duplicate order processing under high-concurrency retail checkout bursts.

## Key Architectural Safeguards
- **Pessimistic Row-Level Locking:** Uses PostgreSQL `SELECT ... FOR UPDATE` (`with_for_update()`) to serialize concurrent reservation requests on the same SKU without blocking unrelated items.
- **Idempotent Request Handling:** Supports `Idempotency-Key` HTTP headers backed by a dedicated persistence table so network retries return identical cached responses without deducting stock twice.
- **Database Integrity Constraints:** Enforces a PostgreSQL `CHECK (available_stock >= 0)` constraint as a final guard against negative inventory.

## Concurrency Benchmark Results (`tests/stress_test.py`)
Simulated **100 simultaneous checkout requests** (`asyncio` + `httpx`) competing for **10 units** of a single SKU:
- **Total Requests:** 100
- **Elapsed Time:** 1.774 seconds
- **Confirmed Orders (`201 Created`):** 10
- **Clean Rejections (`409 Conflict`):** 90
- **Unexpected Errors:** 0
- **Final Database Stock:** 0
- **Idempotency Retry Check:** PASSED

## Quick Start
```bash
docker compose up --build -d
python3 tests/stress_test.py