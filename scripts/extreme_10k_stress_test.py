#!/usr/bin/env python3
"""Extreme 10,000+ Concurrent Multi-Service Stress & Load Testing Engine.

Simulates 10,000+ realistic concurrent users hitting diverse backend services simultaneously:
1. Ultra-fast keep-alive probes (/api/v1/ping, /api/v1/health, /health)
2. Astrologers directory & profile listings (MongoDB aggregations & indexing)
3. Vedic astrology celestial engine (Rashi, Nakshatra, Daily Horoscope transits)
4. Numerology calculations (Chaldean/Pythagorean name & mobile vibration analysis)
5. Vastu 16-zone architectural audit engine
6. Auth lookups & high-CPU bcrypt password verifications
7. Telemetry & error monitoring traces

Usage:
    uv run python scripts/extreme_10k_stress_test.py --requests 10000 --concurrency 60
    uv run python scripts/extreme_10k_stress_test.py --requests 1000 --concurrency 30 --url http://127.0.0.1:8000
"""

import argparse
import asyncio
import math
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

DEFAULT_TARGET = "https://astra-astrology-backend.onrender.com"

TEST_NAMES = [
    "Samiran Samanta",
    "Soumyajit Banerjee",
    "DivinLink Enterprise",
    "Rabindranath Tagore",
    "Subhas Chandra Bose",
    "Alexander The Great",
    "Deepak Chopra",
    "Ananya Mukherjee",
    "Aarav Sengupta",
    "Priyanka Banerjee",
    "Arjun Sharma",
    "Pooja Verma",
]

TEST_MOBILES = [
    "9876543210",
    "9123456780",
    "9988776655",
    "9012345678",
    "9830012345",
    "7003124567",
    "8901234567",
]

TEST_EMAILS = [
    f"test_load_{i}@divinlink.com" for i in range(1, 100)
] + [
    "samiran@ulmind.com",
    "admin@divinlink.com",
    "astrologer@astra.com",
]


@dataclass
class ServiceStats:
    total: int = 0
    success_2xx: int = 0
    client_err_4xx: int = 0
    server_err_5xx: int = 0
    timeouts: int = 0
    latencies_ms: list[float] = field(default_factory=list)


def calculate_percentiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"min": 0, "p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0, "max": 0, "avg": 0}
    s = sorted(values)
    n = len(s)

    def pct(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return s[int(k)]
        return s[f] * (c - k) + s[c] * (k - f)

    return {
        "min": s[0],
        "p50": pct(50),
        "p75": pct(75),
        "p90": pct(90),
        "p95": pct(95),
        "p99": pct(99),
        "max": s[-1],
        "avg": sum(s) / n,
    }


async def execute_task(client: httpx.AsyncClient, base_url: str, task_type: str, timeout: float) -> tuple[str, int, float]:
    start = time.perf_counter()
    status_code = 0

    try:
        if task_type == "ping_health":
            # 15% - Liveness and readiness keep-alive
            sub = random.choice(["/api/v1/ping", "/api/v1/health"])
            resp = await client.get(f"{base_url}{sub}", timeout=timeout)
            status_code = resp.status_code

        elif task_type == "astrologers_dir":
            # 15% - Directory listing & pagination with DB queries
            limit = random.choice([5, 10, 20])
            page = random.choice([1, 2])
            resp = await client.get(f"{base_url}/api/v1/astrologers?limit={limit}&page={page}", timeout=timeout)
            status_code = resp.status_code

        elif task_type == "horoscope_daily":
            # 15% - Daily planetary transits & Vedic horoscope engine
            payload = {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "sign": random.choice(["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces", None]),
                "language": random.choice(["en", "bn", "hi"]),
                "latitude": 22.5726,
                "longitude": 88.3639,
                "timezone": 5.5,
            }
            resp = await client.post(f"{base_url}/api/v1/astrology/horoscope/daily", json=payload, timeout=timeout)
            status_code = resp.status_code

        elif task_type == "astrology_rules":
            # 10% - Rashi, Nakshatra rules & feature pricing
            sub = random.choice(["/api/v1/astrology/rashis", "/api/v1/astrology/nakshatras", "/api/v1/astrology/features/pricing"])
            resp = await client.get(f"{base_url}{sub}", timeout=timeout)
            status_code = resp.status_code

        elif task_type == "numerology_calc":
            # 15% - Numerology Chaldean/Pythagorean algorithms & profile lookups
            num_mode = random.choice(["name", "mobile", "profile"])
            if num_mode == "name":
                payload = {
                    "name": random.choice(TEST_NAMES),
                    "mulank": random.randint(1, 9),
                    "bhagyank": random.randint(1, 9),
                }
                resp = await client.post(f"{base_url}/api/v1/numerology/name", json=payload, timeout=timeout)
            elif num_mode == "mobile":
                payload = {
                    "mobile_number": random.choice(TEST_MOBILES),
                    "mulank": random.randint(1, 9),
                    "bhagyank": random.randint(1, 9),
                }
                resp = await client.post(f"{base_url}/api/v1/numerology/mobile", json=payload, timeout=timeout)
            else:
                num = random.randint(1, 9)
                resp = await client.get(f"{base_url}/api/v1/numerology/profile/{num}", timeout=timeout)
            status_code = resp.status_code

        elif task_type == "vastu_engine":
            # 15% - Vastu 16 zones, 32 padas, compass resolution & remedies
            sub = random.choice([
                "/api/v1/vastu/zones",
                f"/api/v1/vastu/compass/resolve?degree={random.randint(0, 359)}",
                "/api/v1/vastu/compass/padas",
                "/api/v1/vastu/remedies",
                "/api/v1/vastu/astrovastu",
            ])
            resp = await client.get(f"{base_url}{sub}", timeout=timeout)
            status_code = resp.status_code

        elif task_type == "auth_hammer":
            # 10% - Email availability & Bcrypt password verification CPU load
            auth_sub = random.choice(["available", "login"])
            if auth_sub == "available":
                email = random.choice(TEST_EMAILS)
                resp = await client.get(f"{base_url}/api/v1/auth/email/available?email={email}", timeout=timeout)
            else:
                email = random.choice(TEST_EMAILS)
                payload = {"email": email, "password": f"Password@{random.randint(100, 999)}!"}
                resp = await client.post(f"{base_url}/api/v1/auth/login", json=payload, timeout=timeout)
            status_code = resp.status_code

        elif task_type == "telemetry_spike":
            # 5% - Intentional Sentry & Prometheus telemetry error spikes
            resp = await client.get(f"{base_url}/sentry-debug", timeout=timeout)
            status_code = resp.status_code

        else:
            # Fallback ping
            resp = await client.get(f"{base_url}/api/v1/ping", timeout=timeout)
            status_code = resp.status_code

    except (httpx.TimeoutException, asyncio.TimeoutError):
        status_code = -1
    except httpx.RequestError:
        status_code = 0
    except Exception:
        status_code = 0

    duration_ms = (time.perf_counter() - start) * 1000
    return task_type, status_code, duration_ms


async def run_stress_test(
    base_url: str,
    total_requests: int,
    concurrency: int,
    timeout: float,
    dry_run: bool = False,
) -> None:
    print("\n" + "=" * 80)
    print("🔥 DIVINLINK / ASTRA ASTROLOGY — EXTREME 10K+ MULTI-SERVICE STRESS TEST")
    print(f"Target URL:        {base_url}")
    print(f"Total Requests:    {total_requests:,}")
    print(f"Concurrent Users:  {concurrency} parallel async workers")
    print(f"Per-Req Timeout:   {timeout} seconds")
    print(f"Started At:        {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    # Health check probe before starting
    print("\n[1/3] 🔍 Verifying deployment connectivity...")
    limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2)
    async with httpx.AsyncClient(limits=limits) as probe_client:
        try:
            t0 = time.perf_counter()
            r = await probe_client.get(f"{base_url}/api/v1/ping", timeout=10.0)
            ping_ms = (time.perf_counter() - t0) * 1000
            if r.status_code == 200:
                print(f"  ✅ Keep-alive probe responded in {ping_ms:.1f}ms (HTTP 200)")
            else:
                print(f"  ⚠️ Warning: Keep-alive returned HTTP {r.status_code}")
        except Exception as e:
            print(f"  ❌ Error connecting to {base_url}: {e}")
            if not dry_run:
                print("  Aborting load test due to unreachable target.")
                return

    if dry_run:
        print("  Dry-run complete. Exiting without load.")
        return

    # Workload task distribution
    TASK_WEIGHTS = [
        ("ping_health", 0.15),
        ("astrologers_dir", 0.15),
        ("horoscope_daily", 0.15),
        ("astrology_rules", 0.10),
        ("numerology_calc", 0.15),
        ("vastu_engine", 0.15),
        ("auth_hammer", 0.10),
        ("telemetry_spike", 0.05),
    ]

    task_pool: list[str] = []
    for task_name, weight in TASK_WEIGHTS:
        task_pool.extend([task_name] * int(weight * 100))

    queue: asyncio.Queue[str] = asyncio.Queue()
    for _ in range(total_requests):
        queue.put_nowait(random.choice(task_pool))

    services_stats: dict[str, ServiceStats] = defaultdict(ServiceStats)
    all_latencies: list[float] = []
    status_codes_counter: dict[int, int] = defaultdict(int)

    completed = 0
    success_total = 0
    errors_total = 0
    timeouts_total = 0

    lock = asyncio.Lock()
    test_start = time.perf_counter()
    last_print = test_start

    print(f"\n[2/3] 🚀 Launching surge across {concurrency} async workers...")
    print("      (Watch live metrics below; inspect Grafana / Render Dashboard simultaneously)\n")

    async def worker(client: httpx.AsyncClient, worker_id: int) -> None:
        nonlocal completed, success_total, errors_total, timeouts_total, last_print

        while True:
            try:
                task_name = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            task_name, code, duration_ms = await execute_task(client, base_url, task_name, timeout)

            async with lock:
                completed += 1
                status_codes_counter[code] += 1
                all_latencies.append(duration_ms)

                s_stat = services_stats[task_name]
                s_stat.total += 1
                s_stat.latencies_ms.append(duration_ms)

                if 200 <= code < 400:
                    success_total += 1
                    s_stat.success_2xx += 1
                elif code == -1:
                    timeouts_total += 1
                    errors_total += 1
                    s_stat.timeouts += 1
                elif 400 <= code < 500:
                    errors_total += 1
                    s_stat.client_err_4xx += 1
                else:
                    errors_total += 1
                    s_stat.server_err_5xx += 1

                now = time.perf_counter()
                if now - last_print >= 1.0 or completed == total_requests:
                    last_print = now
                    elapsed = now - test_start
                    rps = completed / elapsed if elapsed > 0 else 0
                    pct = (completed / total_requests) * 100
                    success_pct = (success_total / completed * 100) if completed else 0

                    recent_lats = all_latencies[-200:]
                    recent_avg = sum(recent_lats) / len(recent_lats) if recent_lats else 0

                    bar_len = 25
                    filled = int(bar_len * completed / total_requests)
                    bar = "█" * filled + "░" * (bar_len - filled)

                    sys.stdout.write(
                        f"\r  [{bar}] {completed:6,d}/{total_requests:,} ({pct:5.1f}%) | "
                        f"RPS: {rps:5.1f} | 2xx: {success_pct:5.1f}% | "
                        f"Recent Lat: {recent_avg:5.1f}ms | 5xx/Err: {errors_total:3d} | "
                        f"Timeouts: {timeouts_total:2d}"
                    )
                    sys.stdout.flush()

            queue.task_done()

    async with httpx.AsyncClient(limits=limits) as surge_client:
        workers = [asyncio.create_task(worker(surge_client, i)) for i in range(concurrency)]
        await asyncio.gather(*workers)

    test_duration = time.perf_counter() - test_start
    print("\n\n" + "=" * 80)
    print("🏁 [3/3] EXTREME STRESS TEST EXECUTION COMPLETE")
    print("=" * 80)

    global_pcts = calculate_percentiles(all_latencies)
    global_rps = completed / test_duration if test_duration > 0 else 0
    success_rate = (success_total / completed * 100) if completed else 0

    print(f"📊 Global Performance Overview:")
    print(f"  • Total Requests Completed: {completed:,} in {test_duration:.2f} seconds")
    print(f"  • Overall Throughput:       {global_rps:,.1f} requests / second")
    print(f"  • Success Rate (2xx):       {success_total:,} ({success_rate:.2f}%)")
    print(f"  • Failed / Non-2xx:         {errors_total:,} ({100 - success_rate:.2f}%)")
    print(f"  • Timeouts (> {timeout}s):      {timeouts_total:,}")

    print("\n⏱️  Response Latency Distribution (End-to-End):")
    print(f"  • Min:   {global_pcts['min']:6.1f} ms")
    print(f"  • P50:   {global_pcts['p50']:6.1f} ms (Median)")
    print(f"  • P75:   {global_pcts['p75']:6.1f} ms")
    print(f"  • P90:   {global_pcts['p90']:6.1f} ms")
    print(f"  • P95:   {global_pcts['p95']:6.1f} ms")
    print(f"  • P99:   {global_pcts['p99']:6.1f} ms")
    print(f"  • Max:   {global_pcts['max']:6.1f} ms")
    print(f"  • Avg:   {global_pcts['avg']:6.1f} ms")

    print("\n📋 HTTP Status Codes Distribution:")
    for code in sorted(status_codes_counter.keys()):
        label = "Timeout" if code == -1 else ("Network Err" if code == 0 else f"HTTP {code}")
        count = status_codes_counter[code]
        pct = (count / completed * 100) if completed else 0
        print(f"  • {label:<15}: {count:6,d} ({pct:5.1f}%)")

    print("\n🎯 Per-Service Breakdown Matrix:")
    print(f"  {'Service Name':<20} | {'Total':<7} | {'2xx OK':<7} | {'4xx Err':<7} | {'5xx Err':<7} | {'Avg (ms)':<9} | {'P95 (ms)':<9}")
    print("  " + "-" * 76)
    for service_name in sorted(services_stats.keys()):
        stat = services_stats[service_name]
        pcts = calculate_percentiles(stat.latencies_ms)
        print(
            f"  {service_name:<20} | {stat.total:<7,d} | {stat.success_2xx:<7,d} | "
            f"{stat.client_err_4xx:<7,d} | {stat.server_err_5xx:<7,d} | "
            f"{pcts['avg']:9.1f} | {pcts['p95']:9.1f}"
        )

    print("=" * 80)
    print("📈 Live Grafana & Render Monitoring Pointers:")
    print("  1. Render Dashboard:")
    print("     - Check 'CPU Usage %': Look for CPU throttling or spikes during the surge.")
    print("     - Check 'Memory %': Confirm memory remains bounded with zero leaks.")
    print("  2. Grafana Cloud:")
    print("     - Panel 'HTTP Request Rate': Look at the throughput peak.")
    print("     - Panel 'P95 Latency by Endpoint': Inspect which service had the highest latency.")
    print("     - Panel '5xx Exceptions & Sentry Spikes': Verify zero uncaught server crashes.")
    print("=" * 80 + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Astra Backend Extreme 10K+ Multi-Service Stress Testing Engine"
    )
    parser.add_argument(
        "--requests",
        "-n",
        type=int,
        default=10000,
        help="Total requests to fire across all services (default: 10,000)",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=60,
        help="Number of concurrent async worker coroutines (default: 60, up to 500)",
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        default=DEFAULT_TARGET,
        help=f"Target backend URL (default: {DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=15.0,
        help="Per-request timeout in seconds (default: 15.0s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify connection without launching load",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(
            run_stress_test(
                base_url=args.url.rstrip("/"),
                total_requests=args.requests,
                concurrency=args.concurrency,
                timeout=args.timeout,
                dry_run=args.dry_run,
            )
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Stress test interrupted by user.")
        sys.exit(0)
