"""Helper script to test Sentry and Grafana Cloud OpenTelemetry / Loki connectivity."""

import uuid
from datetime import UTC, datetime

import sentry_sdk
from loguru import logger
from sentry_sdk.envelope import Envelope
from sentry_sdk.utils import event_from_exception

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.sentry import init_sentry
from app.core.telemetry import flush_telemetry, init_telemetry


def test_monitoring() -> None:
    setup_logging()
    print("==================================================")
    print(f"Service: {settings.APP_NAME} ({settings.APP_ENV})")
    print(f"Sentry Configured:      {settings.sentry_configured}")
    print(f"Grafana OTel Configured:{settings.otel_configured}")
    print("==================================================")

    # 1. Test Sentry
    if settings.sentry_configured:
        print("[1/2] Testing Sentry error capture...")
        init_sentry()
        client = sentry_sdk.get_client()

        event, _ = event_from_exception(ZeroDivisionError("division by zero (monitoring test)"))
        event["event_id"] = uuid.uuid4().hex
        event["timestamp"] = datetime.now(UTC).isoformat()
        event["platform"] = "python"
        event["logger"] = "fastapi"
        event["transaction"] = "GET /sentry-debug"

        envelope = Envelope(
            headers={"event_id": event["event_id"], "sent_at": datetime.now(UTC).isoformat()}
        )
        envelope.add_event(event)

        url = f"https://{client.transport.parsed_dsn.host}/api/{client.transport.parsed_dsn.project_id}/envelope/"
        body = envelope.serialize()
        headers = {
            "X-Sentry-Auth": client.transport._auth.to_header(),
            "Content-Type": "application/x-sentry-envelope",
        }
        res = client.transport._pool.request("POST", url, headers=headers, body=body, timeout=15.0)
        if res.status == 200:
            print(f"✅ Sentry test error accepted (HTTP 200)! ID: {event['event_id']}")
        else:
            print(f"⚠️ Sentry API responded with status {res.status}: {res.data}")
    else:
        print("⚠️ SENTRY_DSN is not configured.")

    # 2. Test Grafana Cloud OpenTelemetry
    if settings.otel_configured:
        print("\n[2/2] Testing Grafana Cloud OpenTelemetry (Logs, Metrics, RAM/CPU)...")
        init_telemetry()

        # Log via Loguru (streamed to Grafana OTel logs)
        logger.info("Astra Astrology Backend monitoring test event dispatched to Grafana Cloud!")

        # Create a sample span trace
        from opentelemetry import trace
        tracer = trace.get_tracer("monitoring-test")
        with tracer.start_as_current_span("monitoring-health-check") as span:
            span.set_attribute("system.test", "true")
            span.set_attribute("service.name", settings.OTEL_SERVICE_NAME)

        flush_telemetry()
        print("✅ Grafana Cloud OpenTelemetry telemetry dispatched successfully!")
    else:
        print("⚠️ OTEL_EXPORTER_OTLP_* is not configured.")

    print("==================================================")


if __name__ == "__main__":
    test_monitoring()
