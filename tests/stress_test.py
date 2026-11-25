import asyncio
import time
import uuid
import httpx

BASE_URL = "http://localhost:8000"
TEST_SKU = "SKU-CONSOLE-001"
INITIAL_STOCK = 10
CONCURRENT_USERS = 100


async def place_single_order(client: httpx.AsyncClient, request_num: int) -> int:
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    payload = {"sku": TEST_SKU, "quantity": 1}
    response = await client.post("/orders", json=payload, headers=headers)
    return response.status_code


async def run_stress_test():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        seed_payload = {
            "sku": TEST_SKU,
            "name": "Limited Edition Gaming Console",
            "available_stock": INITIAL_STOCK,
        }
        seed_res = await client.post("/products", json=seed_payload)
        assert seed_res.status_code == 201, f"Seed failed: {seed_res.text}"

        print(f"Seeded {TEST_SKU} with {INITIAL_STOCK} units.")
        print(f"Firing {CONCURRENT_USERS} simultaneous checkout requests...")

        start_time = time.perf_counter()
        tasks = [place_single_order(client, i) for i in range(CONCURRENT_USERS)]
        status_codes = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time

        confirmed = status_codes.count(201)
        rejected = status_codes.count(409)
        errors = len(status_codes) - confirmed - rejected

        stock_res = await client.get(f"/products/{TEST_SKU}")
        final_stock = stock_res.json()["available_stock"]

        print("\n--- CONCURRENCY BENCHMARK RESULTS ---")
        print(f"Total Requests:      {CONCURRENT_USERS}")
        print(f"Elapsed Time:        {elapsed:.3f} seconds")
        print(f"Confirmed (201):     {confirmed}")
        print(f"Out of Stock (409):  {rejected}")
        print(f"Unexpected Errors:   {errors}")
        print(f"Final DB Stock:      {final_stock}")

        assert confirmed == INITIAL_STOCK, f"Expected {INITIAL_STOCK} confirmed, got {confirmed}"
        assert rejected == CONCURRENT_USERS - INITIAL_STOCK
        assert final_stock == 0, f"Oversell detected! Stock is {final_stock}"

        duplicate_key = str(uuid.uuid4())
        headers = {"Idempotency-Key": duplicate_key}
        retry_1 = await client.post("/orders", json={"sku": TEST_SKU, "quantity": 1}, headers=headers)
        retry_2 = await client.post("/orders", json={"sku": TEST_SKU, "quantity": 1}, headers=headers)
        assert retry_1.status_code == retry_2.status_code
        assert retry_1.json() == retry_2.json()
        print("Idempotency Retry Check: PASSED (identical response returned)")


if __name__ == "__main__":
    asyncio.run(run_stress_test())