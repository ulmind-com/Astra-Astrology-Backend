"""High-concurrency load testing script for live API performance & memory pressure.

Generates concurrent multi-endpoint traffic against https://astra-astrology-backend.onrender.com
to observe live CPU, RAM, Latency, and Error rates in Grafana and Render Dashboards.
"""

import argparse
import asyncio
import random
import sys
import time

import httpx

BASE_URL = "https://astra-astrology-backend.onrender.com"

NAMES = [
    "Samiran Samanta",
    "Astra Astrology",
    "DivinLink Enterprise",
    "John Doe",
    "Alexander The Great",
    "Rabindranath Tagore",
    "Rohit Sharma",
    "Virat Kohli",
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
    "7003124567",
    "8901234567",
]


async def send_request(client: httpx.AsyncClient, req_type: str) -> tuple[int, float]:
    """Sends a single request and returns (status_code, duration_ms)."""
    start = time.perf_counter()
    status_code = 0
    try:
        if req_type == "root":
            resp = await client.get(f"{BASE_URL}/", timeout=15.0)
            status_code = resp.status_code
        elif req_type == "health":
            resp = await client.get(f"{BASE_URL}/api/v1/health", timeout=15.0)
            status_code = resp.status_code
        elif req_type == "astrologers_db":
            # Real MongoDB query with pagination & filtering
            limit = random.choice([5, 10, 20])
            resp = await client.get(
                f"{BASE_URL}/api/v1/astrologers?limit={limit}", timeout=15.0
            )
            status_code = resp.status_code
        elif req_type == "profile":
            num = random.randint(1, 9)
            resp = await client.get(
                f"{BASE_URL}/api/v1/numerology/profile/{num}", timeout=15.0
            )
            status_code = resp.status_code
        elif req_type == "name_calc":
            # CPU calculation: Chaldean & Pythagorean numerology
            name = random.choice(NAMES)
            payload = {
                "name": name,
                "mulank": random.randint(1, 9),
                "bhagyank": random.randint(1, 9),
            }
            resp = await client.post(
                f"{BASE_URL}/api/v1/numerology/name", json=payload, timeout=15.0
            )
            status_code = resp.status_code
        elif req_type == "mobile_calc":
            # Mobile number compatibility computation
            mob = random.choice(MOBILES)
            payload = {
                "mobile_number": mob,
                "mulank": random.randint(1, 9),
                "bhagyank": random.randint(1, 9),
            }
            resp = await client.post(
                f"{BASE_URL}/api/v1/numerology/mobile", json=payload, timeout=15.0
            )
            status_code = resp.status_code
        elif req_type == "error_trigger":
            # Intentional exception to populate Sentry + Grafana 500 error metrics
            resp = await client.get(f"{BASE_URL}/sentry-debug", timeout=15.0)
            status_code = resp.status_code
    except Exception:
        status_code = 0

    duration_ms = (time.perf_counter() - start) * 1000
    return status_code, duration_ms


async def run_wave(
    client: httpx.AsyncClient, wave_idx: int, concurrency: int, total_waves: int
) -> dict[str, float]:
    """Runs a wave of concurrent mixed requests."""
    endpoints = (
        ["name_calc"] * 5
        + ["mobile_calc"] * 4
        + ["astrologers_db"] * 4
        + ["profile"] * 3
        + ["health"] * 2
        + ["root"] * 1
        + ["error_trigger"] * 1
    )
    random.shuffle(endpoints)

    # Slice to target concurrency
    selected = (endpoints * (concurrency // len(endpoints) + 1))[:concurrency]

    tasks = [send_request(client, ep) for ep in selected]
    wave_start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    wave_duration_s = time.perf_counter() - wave_start

    success_count = sum(1 for status, _ in results if 200 <= status < 300)
    error_count = sum(1 for status, _ in results if status >= 400 or status == 0)
    avg_latency = sum(d for _, d in results) / len(results) if results else 0
    throughput = len(results) / wave_duration_s if wave_duration_s > 0 else 0

    total_str = f"{total_waves}" if total_waves > 0 else "∞"
    print(
        f"⚡ Wave {wave_idx + 1:03d}/{total_str} | "
        f"Sent: {len(results):2d} reqs | "
        f"2xx: {success_count:2d} | 4xx/5xx: {error_count:2d} | "
        f"Avg Latency: {avg_latency:6.1f}ms | Throughput: {throughput:4.1f} req/s"
    )
    return {
        "total": len(results),
        "success": success_count,
        "error": error_count,
        "avg_ms": avg_latency,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Live API High-Concurrency Load Tester")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=15,
        help="Number of concurrent requests per wave (default: 15)",
    )
    parser.add_argument(
        "--waves",
        type=int,
        default=60,
        help="Number of waves to send (default: 60, set to 0 for infinite)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay in seconds between waves (default: 0.2)",
    )
    args = parser.parse_args()

    concurrency = args.concurrency
    total_waves = args.waves
    delay = args.delay

    print("==================================================================")
    print("🔥 Starting High-Concurrency Live Performance & Stress Test")
    print(f"Target URL:  {BASE_URL}")
    print(f"Concurrency: {concurrency} concurrent requests per wave")
    waves_desc = "Infinite (Ctrl+C to stop)" if total_waves == 0 else f"{total_waves} waves"
    print(f"Total Waves: {waves_desc}")
    print("Workloads:   Numerology CPU calculation, MongoDB aggregations,")
    print("             Health probes, and live Sentry/Grafana error traces")
    print("==================================================================")

    limits = httpx.Limits(
        max_keepalive_connections=concurrency * 2,
        max_connections=concurrency * 3,
    )
    wave_idx = 0
    total_sent = 0
    total_2xx = 0
    total_err = 0

    try:
        async with httpx.AsyncClient(limits=limits) as client:
            while total_waves == 0 or wave_idx < total_waves:
                stats = await run_wave(client, wave_idx, concurrency, total_waves)
                total_sent += int(stats["total"])
                total_2xx += int(stats["success"])
                total_err += int(stats["error"])
                wave_idx += 1
                if delay > 0:
                    await asyncio.sleep(delay)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user.")

    print("\n==================================================================")
    print("📊 Stress Test Summary:")
    print(f"  • Total Waves Completed: {wave_idx}")
    print(f"  • Total Requests Sent:   {total_sent}")
    success_pct = (total_2xx / total_sent * 100) if total_sent else 0
    print(f"  • Successful (2xx):      {total_2xx} ({success_pct:.1f}%)")
    print(f"  • Errors / 500s:         {total_err}")
    print("==================================================================")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
