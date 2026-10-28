"""Enterprise Multi-Stage Stress & Load Testing Suite.

Simulates:
1. Single IP Flood (5,000 rapid requests - DDoS / Attack detection test)
2. Concurrent Auth & MongoDB Hammer (Login & Email lookups - DB & Bcrypt CPU test)
3. 10,000 Multi-User Surge (Complex mixed-traffic performance benchmark)

Targets live deployment: https://astra-astrology-backend.onrender.com
"""

import argparse
import asyncio
import random
import sys
import time

import httpx

BASE_URL = "https://astra-astrology-backend.onrender.com"

TEST_EMAILS = [
    f"test_user_{i}@divinlink.com" for i in range(1, 50)
] + [
    "samiran@ulmind.com",
    "admin@divinlink.com",
    "astrologer@astra.com",
    "contact@divinlink.com",
]

NAMES = [
    "Samiran Samanta",
    "Astra Astrology",
    "DivinLink Enterprise",
    "Alexander The Great",
    "Rabindranath Tagore",
    "Subhas Chandra Bose",
    "Deepak Chopra",
    "Ananya Mukherjee",
    "Aarav Sengupta",
    "Priyanka Banerjee",
]

MOBILES = [
    "9876543210",
    "9123456780",
    "9988776655",
    "9012345678",
    "9830012345",
]


# =====================================================================
# STAGE 1: Single IP Flood / DDoS Simulation
# =====================================================================
async def run_single_ip_flood(total_reqs: int = 5000, concurrency: int = 40) -> None:
    print("\n" + "=" * 70)
    print("🚨 STAGE 1: SINGLE IP FLOOD & ATTACK SIMULATION")
    print(f"Goal: Send {total_reqs:,} rapid requests from this single IP")
    print(f"Concurrency: {concurrency} workers | Target: {BASE_URL}")
    print("Watch Grafana 'Top Requesting IPs' panel turn RED with this IP!")
    print("=" * 70)

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(total_reqs):
        queue.put_nowait(i)

    success = 0
    errors = 0
    start_time = time.perf_counter()

    async def worker(client: httpx.AsyncClient) -> None:
        nonlocal success, errors
        while not queue.empty():
            try:
                _ = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            # Fast endpoints to simulate high-rate flood
            ep = random.choice([
                f"{BASE_URL}/",
                f"{BASE_URL}/api/v1/health",
                f"{BASE_URL}/api/v1/auth/email/available?email={random.choice(TEST_EMAILS)}",
            ])
            try:
                resp = await client.get(ep, timeout=10.0)
                if 200 <= resp.status_code < 400:
                    success += 1
                else:
                    errors += 1
            except Exception:
                errors += 1
            finally:
                queue.task_done()

            # Progress milestone every 500 requests
            done = success + errors
            if done % 500 == 0 or done == total_reqs:
                elapsed = time.perf_counter() - start_time
                rps = done / elapsed if elapsed > 0 else 0
                pct = (done / total_reqs) * 100
                print(
                    f"  💥 Flood Progress: {done:5d}/{total_reqs} ({pct:5.1f}%) | "
                    f"Throughput: {rps:5.1f} req/s | 2xx: {success} | Errors: {errors}"
                )

    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [asyncio.create_task(worker(client)) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    duration = time.perf_counter() - start_time
    print(f"✅ Stage 1 Complete in {duration:.1f}s | Avg Speed: {total_reqs / duration:.1f} req/s")


# =====================================================================
# STAGE 2: Mass Concurrent Login & MongoDB Auth Hammer
# =====================================================================
async def run_auth_db_hammer(total_reqs: int = 1500, concurrency: int = 25) -> None:
    print("\n" + "=" * 70)
    print("🔐 STAGE 2: CONCURRENT LOGIN & MONGODB AUTH HAMMER")
    print(f"Goal: {total_reqs:,} auth/db queries to test MongoDB lookups & bcrypt CPU load")
    print(f"Concurrency: {concurrency} workers")
    print("Watch Grafana Database Query Latency & Sentry Queries!")
    print("=" * 70)

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(total_reqs):
        queue.put_nowait(i)

    results: list[tuple[int, float]] = []
    start_time = time.perf_counter()

    async def worker(client: httpx.AsyncClient) -> None:
        while not queue.empty():
            try:
                _ = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            t0 = time.perf_counter()
            code = 0
            if random.random() < 0.6:
                # Login attempt: Triggers MongoDB user lookup + password check
                email = random.choice(TEST_EMAILS)
                payload = {"email": email, "password": f"Password@{random.randint(100, 999)}!"}
                try:
                    resp = await client.post(
                        f"{BASE_URL}/api/v1/auth/login", json=payload, timeout=12.0
                    )
                    code = resp.status_code
                except Exception:
                    code = 0
            else:
                # Email availability: Triggers MongoDB check_email_available
                email = f"avail_{random.randint(1000, 9999)}@divinlink.com"
                try:
                    resp = await client.get(
                        f"{BASE_URL}/api/v1/auth/email/available?email={email}", timeout=12.0
                    )
                    code = resp.status_code
                except Exception:
                    code = 0

            ms = (time.perf_counter() - t0) * 1000
            results.append((code, ms))
            queue.task_done()

            done = len(results)
            if done % 250 == 0 or done == total_reqs:
                avg_ms = sum(x[1] for x in results[-250:]) / min(done, 250)
                print(
                    f"  🔑 Auth Hammer: {done:4d}/{total_reqs} | "
                    f"Recent Avg Latency: {avg_ms:6.1f}ms"
                )

    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [asyncio.create_task(worker(client)) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    duration = time.perf_counter() - start_time
    avg_total = sum(x[1] for x in results) / len(results) if results else 0
    print(
        f"✅ Stage 2 Complete in {duration:.1f}s | Avg Auth Latency: {avg_total:.1f}ms | "
        f"Rate: {total_reqs / duration:.1f} queries/s"
    )


# =====================================================================
# STAGE 3: 10,000 Multi-User Surge (Complex Mixed Traffic)
# =====================================================================
async def run_full_surge(total_reqs: int = 10000, concurrency: int = 35) -> None:
    print("\n" + "=" * 70)
    print("🌊 STAGE 3: 10,000 MULTI-USER FULL APPLICATION SURGE")
    print(f"Goal: {total_reqs:,} complex requests across the entire application stack")
    print(f"Concurrency: {concurrency} parallel users")
    print("Workloads: Numerology CPU crunching, MongoDB Directory Aggregations,")
    print("           Profile Lookups, System Health, and Error Traces")
    print("=" * 70)

    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    queue: asyncio.Queue[str] = asyncio.Queue()

    # Build balanced mix of 10,000 requests
    for _ in range(total_reqs):
        r = random.random()
        if r < 0.35:
            queue.put_nowait("numerology_name")
        elif r < 0.60:
            queue.put_nowait("numerology_mobile")
        elif r < 0.80:
            queue.put_nowait("astrologers_db")
        elif r < 0.92:
            queue.put_nowait("profile")
        elif r < 0.98:
            queue.put_nowait("health")
        else:
            queue.put_nowait("error_trigger")

    results: list[tuple[int, float]] = []
    start_time = time.perf_counter()

    async def worker(client: httpx.AsyncClient) -> None:
        while not queue.empty():
            try:
                task_type = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            t0 = time.perf_counter()
            code = 0
            try:
                if task_type == "numerology_name":
                    payload = {
                        "name": random.choice(NAMES),
                        "mulank": random.randint(1, 9),
                        "bhagyank": random.randint(1, 9),
                    }
                    resp = await client.post(
                        f"{BASE_URL}/api/v1/numerology/name", json=payload, timeout=15.0
                    )
                    code = resp.status_code
                elif task_type == "numerology_mobile":
                    payload = {
                        "mobile_number": random.choice(MOBILES),
                        "mulank": random.randint(1, 9),
                        "bhagyank": random.randint(1, 9),
                    }
                    resp = await client.post(
                        f"{BASE_URL}/api/v1/numerology/mobile", json=payload, timeout=15.0
                    )
                    code = resp.status_code
                elif task_type == "astrologers_db":
                    limit = random.choice([5, 10, 20])
                    resp = await client.get(
                        f"{BASE_URL}/api/v1/astrologers?limit={limit}", timeout=15.0
                    )
                    code = resp.status_code
                elif task_type == "profile":
                    num = random.randint(1, 9)
                    resp = await client.get(
                        f"{BASE_URL}/api/v1/numerology/profile/{num}", timeout=15.0
                    )
                    code = resp.status_code
                elif task_type == "health":
                    resp = await client.get(f"{BASE_URL}/api/v1/health", timeout=15.0)
                    code = resp.status_code
                elif task_type == "error_trigger":
                    resp = await client.get(f"{BASE_URL}/sentry-debug", timeout=15.0)
                    code = resp.status_code
            except Exception:
                code = 0

            ms = (time.perf_counter() - t0) * 1000
            results.append((code, ms))
            queue.task_done()

            done = len(results)
            if done % 1000 == 0 or done == total_reqs:
                recent = results[-1000:]
                avg_recent = sum(x[1] for x in recent) / len(recent)
                success_recent = sum(1 for x in recent if 200 <= x[0] < 400)
                elapsed = time.perf_counter() - start_time
                throughput = done / elapsed if elapsed > 0 else 0
                pct = (done / total_reqs) * 100
                print(
                    f"  🌊 Surge Progress: {done:5d}/{total_reqs} ({pct:5.1f}%) | "
                    f"Throughput: {throughput:4.1f} req/s | "
                    f"Recent Avg Latency: {avg_recent:6.1f}ms | 2xx: {success_recent}/1000"
                )

    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [asyncio.create_task(worker(client)) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    duration = time.perf_counter() - start_time
    total_count = len(results)
    success_count = sum(1 for x in results if 200 <= x[0] < 400)
    error_count = sum(1 for x in results if x[0] >= 400 or x[0] == 0)
    avg_latency = sum(x[1] for x in results) / total_count if total_count else 0
    success_pct = (success_count / total_count * 100) if total_count else 0

    print("\n" + "=" * 70)
    print("🏆 10,000 MULTI-USER SURGE TEST RESULTS:")
    print(f"  • Total Requests Executed: {total_count:,}")
    print(f"  • Successful Responses:    {success_count:,} ({success_pct:.1f}%)")
    print(f"  • Errors / 5xx Exceptions: {error_count:,}")
    print(f"  • Total Duration:          {duration:.1f} seconds (~{duration / 60:.1f} minutes)")
    print(f"  • Global Throughput:       {total_count / duration:.1f} requests/second")
    print(f"  • Average Latency:         {avg_latency:.1f} ms")
    print("==================================================================")


# =====================================================================
# MAIN RUNNER
# =====================================================================
async def main() -> None:
    parser = argparse.ArgumentParser(description="Astra Backend Enterprise Stress Tester")
    parser.add_argument(
        "--mode",
        choices=["ddos", "auth", "surge", "all"],
        default="all",
        help="Stress mode: ddos, auth (MongoDB login), surge (multi-user), or all",
    )
    parser.add_argument(
        "--flood-count",
        type=int,
        default=3000,
        help="Requests for DDoS IP flood (default: 3000)",
    )
    parser.add_argument(
        "--auth-count",
        type=int,
        default=1000,
        help="Requests for Auth/DB hammer (default: 1000)",
    )
    parser.add_argument(
        "--surge-count",
        type=int,
        default=5000,
        help="Requests for Multi-User surge (default: 5000, up to 10000)",
    )
    args = parser.parse_args()

    mode = args.mode
    print("==================================================================")
    print("🚀 Astra Astrology Backend — Enterprise Stress Test Runner")
    print(f"Target Service: {BASE_URL}")
    print(f"Selected Mode:  {mode.upper()}")
    print("==================================================================")

    if mode in ("ddos", "all"):
        await run_single_ip_flood(total_reqs=args.flood_count, concurrency=35)
        if mode == "all":
            await asyncio.sleep(2)

    if mode in ("auth", "all"):
        await run_auth_db_hammer(total_reqs=args.auth_count, concurrency=25)
        if mode == "all":
            await asyncio.sleep(2)

    if mode in ("surge", "all"):
        await run_full_surge(total_reqs=args.surge_count, concurrency=35)

    print("\n🎉 ALL ENTERPRISE STRESS TESTS COMPLETED!")
    print("Check your Grafana Cloud and Sentry dashboards now to see the full telemetry!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")
        sys.exit(0)
