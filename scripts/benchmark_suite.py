"""Unified Enterprise Performance, Stress & Observability Benchmark Suite.

Interactive and automated load generator for Astra Astrology Backend
(https://astra-astrology-backend.onrender.com).

Modes:
1. Full Enterprise Suite (DDoS -> Auth Hammer -> Ramp-Up -> Surge)
2. Single-IP Flood / DDoS Simulation
3. Concurrent Login & MongoDB Auth Hammer
4. Ramp-Up / Breaking-Point Stress Test (Gradual step increase)
5. Instantaneous Spike / Flash-Crowd Test (Sudden burst)
6. Sequential Step-by-Step Drip (1-by-1 baseline latency)
7. Custom Endpoint Targeting
"""

import argparse
import asyncio
import json
import math
import random
import sys
import time
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://astra-astrology-backend.onrender.com"

# Sample realistic payload pools
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
    "7003124567",
    "8901234567",
]

EMAILS = [
    f"benchmark_user_{i}@divinlink.com" for i in range(1, 100)
] + ["samiran@ulmind.com", "admin@divinlink.com"]


# ANSI Color Codes
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


class BenchmarkTracker:
    """Thread-safe collector for request performance and latency metrics."""

    def __init__(self, total_expected: int) -> None:
        self.total_expected = total_expected
        self.results: list[tuple[int, float, str]] = []  # (status, duration_ms, endpoint)
        self.start_time = time.perf_counter()
        self.end_time = 0.0

    def record(self, status: int, duration_ms: float, endpoint: str) -> None:
        self.results.append((status, duration_ms, endpoint))

    def finish(self) -> None:
        self.end_time = time.perf_counter()

    @property
    def total_completed(self) -> int:
        return len(self.results)

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time if self.end_time > 0 else time.perf_counter()
        return max(end - self.start_time, 0.001)

    @property
    def throughput(self) -> float:
        return self.total_completed / self.elapsed_seconds

    def compute_stats(self) -> dict[str, Any]:
        if not self.results:
            return {}

        latencies = sorted(x[1] for x in self.results)
        n = len(latencies)

        def percentile(p: float) -> float:
            idx = min(int(math.ceil(p * n)) - 1, n - 1)
            return latencies[max(0, idx)]

        success_count = sum(1 for status, _, _ in self.results if 200 <= status < 400)
        client_err_count = sum(1 for status, _, _ in self.results if 400 <= status < 500)
        server_err_count = sum(1 for status, _, _ in self.results if status >= 500)
        network_err_count = sum(1 for status, _, _ in self.results if status == 0)

        return {
            "total_sent": n,
            "success_2xx": success_count,
            "client_error_4xx": client_err_count,
            "server_error_5xx": server_err_count,
            "network_errors": network_err_count,
            "elapsed_s": self.elapsed_seconds,
            "throughput_rps": self.throughput,
            "min_ms": latencies[0],
            "avg_ms": sum(latencies) / n,
            "p50_ms": percentile(0.50),
            "p90_ms": percentile(0.90),
            "p95_ms": percentile(0.95),
            "p99_ms": percentile(0.99),
            "max_ms": latencies[-1],
        }

    def print_summary(self, stage_name: str) -> None:
        stats = self.compute_stats()
        if not stats:
            print(f"{Colors.RED}No requests recorded.{Colors.RESET}")
            return

        total = stats["total_sent"]
        succ = stats["success_2xx"]
        pct = (succ / total * 100) if total else 0

        print("\n" + "=" * 72)
        print(f"{Colors.BOLD}{Colors.CYAN}📊 BENCHMARK REPORT: {stage_name.upper()}{Colors.RESET}")
        print("=" * 72)
        print(f"  • Total Requests Sent:   {Colors.BOLD}{total:,}{Colors.RESET}")
        print(f"  • Successful (2xx/3xx):  {Colors.GREEN}{succ:,} ({pct:.1f}%){Colors.RESET}")
        print(
            f"  • Client Handled (4xx):  "
            f"{Colors.YELLOW}{stats['client_error_4xx']:,}{Colors.RESET}"
        )
        print(
            f"  • Server Errors (5xx):   "
            f"{Colors.RED}{stats['server_error_5xx']:,}{Colors.RESET}"
        )
        print(
            f"  • Network Drops/Timeouts:"
            f"{Colors.RED}{stats['network_errors']:,}{Colors.RESET}"
        )
        print(
            f"  • Total Execution Time:  "
            f"{Colors.BOLD}{stats['elapsed_s']:.2f} seconds{Colors.RESET}"
        )
        print(
            f"  • Average Throughput:    "
            f"{Colors.BOLD}{Colors.GREEN}{stats['throughput_rps']:.1f} req/s{Colors.RESET}"
        )
        print("-" * 72)
        print(f"{Colors.BOLD}Latency Distribution:{Colors.RESET}")
        print(
            f"  • Min: {stats['min_ms']:6.1f} ms  |  Avg: {stats['avg_ms']:6.1f} ms  |  "
            f"Max: {stats['max_ms']:6.1f} ms"
        )
        print(
            f"  • P50: {stats['p50_ms']:6.1f} ms  |  P90: {stats['p90_ms']:6.1f} ms  |  "
            f"P95: {stats['p95_ms']:6.1f} ms  |  P99: {stats['p99_ms']:6.1f} ms"
        )
        print("=" * 72 + "\n")


# =====================================================================
# REQUEST EXECUTION HELPERS
# =====================================================================
async def dispatch_request(
    client: httpx.AsyncClient, base_url: str, request_kind: str
) -> tuple[int, float, str]:
    """Sends a typed request and returns (status_code, latency_ms, endpoint_name)."""
    t0 = time.perf_counter()
    status = 0
    endpoint_label = request_kind

    try:
        if request_kind == "health":
            resp = await client.get(f"{base_url}/api/v1/health", timeout=12.0)
            status = resp.status_code
        elif request_kind == "root":
            resp = await client.get(f"{base_url}/", timeout=10.0)
            status = resp.status_code
        elif request_kind == "auth_avail":
            email = random.choice(EMAILS)
            resp = await client.get(
                f"{base_url}/api/v1/auth/email/available?email={email}", timeout=12.0
            )
            status = resp.status_code
        elif request_kind == "auth_login":
            payload = {
                "email": random.choice(EMAILS),
                "password": f"Pass@{random.randint(100, 999)}!",
            }
            resp = await client.post(f"{base_url}/api/v1/auth/login", json=payload, timeout=15.0)
            status = resp.status_code
        elif request_kind == "numerology_name":
            payload = {
                "name": random.choice(NAMES),
                "mulank": random.randint(1, 9),
                "bhagyank": random.randint(1, 9),
            }
            resp = await client.post(
                f"{base_url}/api/v1/numerology/name", json=payload, timeout=15.0
            )
            status = resp.status_code
        elif request_kind == "numerology_mobile":
            payload = {
                "mobile_number": random.choice(MOBILES),
                "mulank": random.randint(1, 9),
                "bhagyank": random.randint(1, 9),
            }
            resp = await client.post(
                f"{base_url}/api/v1/numerology/mobile", json=payload, timeout=15.0
            )
            status = resp.status_code
        elif request_kind == "astrologers_db":
            limit = random.choice([5, 10, 20])
            resp = await client.get(
                f"{base_url}/api/v1/astrologers?limit={limit}", timeout=15.0
            )
            status = resp.status_code
        elif request_kind == "profile":
            num = random.randint(1, 9)
            resp = await client.get(
                f"{base_url}/api/v1/numerology/profile/{num}", timeout=12.0
            )
            status = resp.status_code
        elif request_kind == "error_trigger":
            resp = await client.get(f"{base_url}/sentry-debug", timeout=10.0)
            status = resp.status_code
        else:
            # Custom raw path
            resp = await client.get(f"{base_url}{request_kind}", timeout=12.0)
            status = resp.status_code
    except Exception:
        status = 0

    latency_ms = (time.perf_counter() - t0) * 1000
    return status, latency_ms, endpoint_label


# =====================================================================
# BENCHMARK SUITE MODES
# =====================================================================
async def run_pool_test(
    base_url: str,
    kinds: list[str],
    total_reqs: int,
    concurrency: int,
    stage_name: str,
    delay_between_waves: float = 0.0,
) -> BenchmarkTracker:
    """Generic concurrent worker pool test."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ Launching: {stage_name}{Colors.RESET}")
    print(f"  Target: {base_url}")
    print(f"  Total Requests: {total_reqs:,} | Concurrency: {concurrency} workers")
    if delay_between_waves > 0:
        print(f"  Pacing: {delay_between_waves}s pause between tasks")

    tracker = BenchmarkTracker(total_reqs)
    queue: asyncio.Queue[str] = asyncio.Queue()
    for _ in range(total_reqs):
        queue.put_nowait(random.choice(kinds))

    limits = httpx.Limits(
        max_keepalive_connections=concurrency * 2, max_connections=concurrency * 3
    )

    async def worker(client: httpx.AsyncClient) -> None:
        while not queue.empty():
            try:
                kind = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            status, ms, ep = await dispatch_request(client, base_url, kind)
            tracker.record(status, ms, ep)
            queue.task_done()

            # Dynamic progress updates
            done = tracker.total_completed
            step = 100 if total_reqs <= 1000 else (500 if total_reqs <= 5000 else 1000)
            if done % step == 0 or done == total_reqs:
                pct = (done / total_reqs) * 100
                rps = tracker.throughput
                recent_avg = (
                    sum(x[1] for x in tracker.results[-step:]) / min(done, step)
                    if done
                    else 0
                )
                prefix = f"  {Colors.CYAN}⚡ [{stage_name[:10]}]"
                print(
                    f"{prefix} Done: {done:5d}/{total_reqs} ({pct:5.1f}%) | "
                    f"RPS: {rps:5.1f} | Recent Avg: {recent_avg:6.1f} ms{Colors.RESET}"
                )

            if delay_between_waves > 0:
                await asyncio.sleep(delay_between_waves)

    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [asyncio.create_task(worker(client)) for _ in range(concurrency)]
        await asyncio.gather(*tasks)

    tracker.finish()
    tracker.print_summary(stage_name)
    return tracker


async def run_sequential_drip(base_url: str, total_reqs: int = 50) -> BenchmarkTracker:
    """Runs single requests one-by-one to measure pure, un-congested baseline latency."""
    msg = f"\n{Colors.BOLD}{Colors.YELLOW}▶ Sequential Drip (Baseline Latency){Colors.RESET}"
    print(msg)
    print(f"  Target: {base_url} | Total: {total_reqs} requests (1 at a time)")

    tracker = BenchmarkTracker(total_reqs)
    endpoints = ["health", "auth_avail", "numerology_name", "astrologers_db", "profile"]

    async with httpx.AsyncClient() as client:
        for i in range(total_reqs):
            kind = random.choice(endpoints)
            status, ms, ep = await dispatch_request(client, base_url, kind)
            tracker.record(status, ms, ep)
            code_col = Colors.GREEN if 200 <= status < 400 else Colors.RED
            print(
                f"  [{i + 1:03d}/{total_reqs}] {ep:16s} -> "
                f"{code_col}{status}{Colors.RESET} in {ms:6.1f} ms"
            )
            await asyncio.sleep(0.1)

    tracker.finish()
    tracker.print_summary("Sequential Baseline Latency")
    return tracker


async def run_ramp_up_stress(
    base_url: str, max_concurrency: int = 60, step: int = 15, reqs_per_step: int = 200
) -> None:
    """Ramps up concurrency step-by-step to detect server saturation/breaking point."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ Launching: Step Ramp-Up Saturation Test{Colors.RESET}")
    print(f"  Target: {base_url} | Ramping up to {max_concurrency} workers in steps of +{step}")

    kinds = ["numerology_name", "numerology_mobile", "astrologers_db", "health"]
    current_concurrency = step

    while current_concurrency <= max_concurrency:
        await run_pool_test(
            base_url=base_url,
            kinds=kinds,
            total_reqs=reqs_per_step,
            concurrency=current_concurrency,
            stage_name=f"Ramp Step ({current_concurrency} workers)",
            delay_between_waves=0.0,
        )
        current_concurrency += step
        await asyncio.sleep(1)


async def run_burst_spike(
    base_url: str, spike_concurrency: int = 60, total_spike_reqs: int = 300
) -> None:
    """Fires a sudden burst of requests all at once."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}▶ Launching: Flash-Spike Burst Test{Colors.RESET}")
    print(f"  Simulating instant rush of {total_spike_reqs} simultaneous users!")
    await run_pool_test(
        base_url=base_url,
        kinds=["health", "numerology_name", "astrologers_db", "auth_login"],
        total_reqs=total_spike_reqs,
        concurrency=spike_concurrency,
        stage_name="Instantaneous Spike Burst",
        delay_between_waves=0.0,
    )


# =====================================================================
# INTERACTIVE CLI PROMPT
# =====================================================================
def prompt_user_interactive() -> dict[str, Any]:
    print("\n" + "=" * 72)
    header = f"{Colors.BOLD}{Colors.HEADER}🌌 ASTRA ASTROLOGY BACKEND — BENCHMARK{Colors.RESET}"
    print(header)
    print(f"{Colors.DIM}Targeting Render Free Tier & Grafana Cloud Observability{Colors.RESET}")
    print("=" * 72)
    print(f"{Colors.BOLD}Select a Test Mode:{Colors.RESET}")
    print(f"  {Colors.CYAN}[1]{Colors.RESET} 🏆 {Colors.BOLD}Enterprise Suite{Colors.RESET}")
    print(f"  {Colors.CYAN}[2]{Colors.RESET} 🚨 {Colors.BOLD}Single-IP Flood{Colors.RESET}")
    print(f"  {Colors.CYAN}[3]{Colors.RESET} 🔐 {Colors.BOLD}Login & DB Hammer{Colors.RESET}")
    print(f"  {Colors.CYAN}[4]{Colors.RESET} 🌊 {Colors.BOLD}Full App Surge{Colors.RESET}")
    print(f"  {Colors.CYAN}[5]{Colors.RESET} 📈 {Colors.BOLD}Ramp-Up Breaking Test{Colors.RESET}")
    print(f"  {Colors.CYAN}[6]{Colors.RESET} ⚡ {Colors.BOLD}Instant Spike Burst{Colors.RESET}")
    print(f"  {Colors.CYAN}[7]{Colors.RESET} 🚶 {Colors.BOLD}Sequential Drip{Colors.RESET}")
    print(f"  {Colors.CYAN}[8]{Colors.RESET} 🎯 {Colors.BOLD}Custom Endpoint{Colors.RESET}")
    print("-" * 72)

    choice = input(f"{Colors.BOLD}Enter choice [1-8] (default: 1): {Colors.RESET}").strip() or "1"

    url = input(
        f"{Colors.BOLD}Enter target URL (default: {DEFAULT_BASE_URL}): {Colors.RESET}"
    ).strip() or DEFAULT_BASE_URL

    concurrency = 30
    total = 2000

    if choice in ("2", "3", "4", "8"):
        c_in = input(
            f"{Colors.BOLD}Enter concurrency workers (default: 30): {Colors.RESET}"
        ).strip()
        if c_in.isdigit():
            concurrency = int(c_in)

        t_prompt = f"{Colors.BOLD}Enter total requests to send (default: 2000): {Colors.RESET}"
        t_in = input(t_prompt).strip()
        if t_in.isdigit():
            total = int(t_in)

    custom_path = "/api/v1/health"
    if choice == "8":
        custom_path = input(
            f"{Colors.BOLD}Enter endpoint path (e.g., /api/v1/astrologers): {Colors.RESET}"
        ).strip() or "/api/v1/health"

    return {
        "choice": choice,
        "url": url.rstrip("/"),
        "concurrency": concurrency,
        "total": total,
        "custom_path": custom_path,
    }


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================
async def main() -> None:
    parser = argparse.ArgumentParser(description="Astra Backend Benchmark & Load Tester")
    parser.add_argument(
        "--mode",
        choices=["interactive", "all", "ddos", "auth", "surge", "ramp", "spike", "drip", "custom"],
        default="interactive",
        help="Test mode to execute (default: interactive prompt)",
    )
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Target backend base URL")
    parser.add_argument("--concurrency", type=int, default=30, help="Concurrent workers")
    parser.add_argument("--total", type=int, default=2000, help="Total requests to send")
    parser.add_argument("--path", default="/api/v1/health", help="Custom path for custom mode")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay between tasks in seconds")
    parser.add_argument("--json-out", default="", help="Optional path to write JSON report")

    args = parser.parse_args()

    mode = args.mode
    base_url = args.url.rstrip("/")
    concurrency = args.concurrency
    total = args.total
    custom_path = args.path
    delay = args.delay

    # If no args were supplied, launch rich interactive prompt
    if len(sys.argv) == 1 or mode == "interactive":
        config = prompt_user_interactive()
        ch = config["choice"]
        base_url = config["url"]
        concurrency = config["concurrency"]
        total = config["total"]
        custom_path = config["custom_path"]

        mapping = {
            "1": "all",
            "2": "ddos",
            "3": "auth",
            "4": "surge",
            "5": "ramp",
            "6": "spike",
            "7": "drip",
            "8": "custom",
        }
        mode = mapping.get(ch, "all")

    print("\n" + "=" * 72)
    print(f"{Colors.BOLD}{Colors.GREEN}🔥 STARTING BENCHMARK: {mode.upper()}{Colors.RESET}")
    print(f"  Target URL:   {base_url}")
    print(f"  Concurrency:  {concurrency} workers")
    print(f"  Requests:     {total:,} total")
    print("==================================================================")

    reports: dict[str, Any] = {}

    if mode in ("ddos", "all"):
        kinds = ["root", "health", "auth_avail"]
        t = await run_pool_test(
            base_url,
            kinds,
            total_reqs=3000 if mode == "all" else total,
            concurrency=concurrency,
            stage_name="Single-IP DDoS Flood",
            delay_between_waves=delay,
        )
        reports["ddos"] = t.compute_stats()
        if mode == "all":
            await asyncio.sleep(2)

    if mode in ("auth", "all"):
        kinds = ["auth_login", "auth_avail"]
        t = await run_pool_test(
            base_url,
            kinds,
            total_reqs=1000 if mode == "all" else total,
            concurrency=min(concurrency, 25),
            stage_name="Auth & MongoDB Hammer",
            delay_between_waves=delay,
        )
        reports["auth"] = t.compute_stats()
        if mode == "all":
            await asyncio.sleep(2)

    if mode in ("ramp", "all"):
        await run_ramp_up_stress(base_url, max_concurrency=45, step=15, reqs_per_step=150)
        if mode == "all":
            await asyncio.sleep(2)

    if mode in ("spike",):
        await run_burst_spike(base_url, spike_concurrency=concurrency, total_spike_reqs=total)

    if mode in ("drip",):
        t = await run_sequential_drip(base_url, total_reqs=min(total, 100))
        reports["drip"] = t.compute_stats()

    if mode in ("custom",):
        t = await run_pool_test(
            base_url,
            [custom_path],
            total_reqs=total,
            concurrency=concurrency,
            stage_name=f"Custom Endpoint ({custom_path})",
            delay_between_waves=delay,
        )
        reports["custom"] = t.compute_stats()

    if mode in ("surge", "all"):
        kinds = [
            "numerology_name",
            "numerology_mobile",
            "astrologers_db",
            "profile",
            "health",
            "error_trigger",
        ]
        t = await run_pool_test(
            base_url,
            kinds,
            total_reqs=5000 if mode == "all" else total,
            concurrency=concurrency,
            stage_name="Multi-User Complex Surge",
            delay_between_waves=delay,
        )
        reports["surge"] = t.compute_stats()

    print(f"\n{Colors.BOLD}{Colors.GREEN}✨ BENCHMARKS COMPLETED SUCCESSFULLY!{Colors.RESET}")
    print(f"{Colors.CYAN}Grafana Cloud: https://braveangelfish3296.grafana.net{Colors.RESET}")
    print(f"{Colors.CYAN}Render Metrics: https://dashboard.render.com{Colors.RESET}")

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(reports, f, indent=2)
        print(f"Report saved to {args.json_out}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Benchmark halted by user.{Colors.RESET}")
        sys.exit(0)
