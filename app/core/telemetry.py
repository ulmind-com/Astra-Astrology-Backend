"""Production-grade OpenTelemetry setup for Grafana Cloud.

Streams:
1. Metrics: API latency, request count, HTTP status codes, and Host/Process RAM & CPU.
2. Traces: Full APM tracing of endpoints and database queries.
3. Logs: Loguru logs forwarded to Grafana Cloud OpenTelemetry log stream.
"""

import contextlib
from typing import Any

from fastapi import FastAPI
from loguru import logger
from opentelemetry import metrics, trace
from opentelemetry._logs import LogRecord, SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings

_log_provider: LoggerProvider | None = None
_otel_logger: Any = None


def _parse_headers(header_str: str) -> dict[str, str]:
    """Parse comma-separated or key=value header string."""
    headers: dict[str, str] = {}
    if not header_str:
        return headers
    for part in header_str.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            headers[k.strip()] = v.strip()
    return headers


def _loguru_to_otel_sink(message: Any) -> None:
    """Forward Loguru log records to OpenTelemetry logger."""
    global _otel_logger
    if not _otel_logger:
        return
    try:
        record = message.record
        level_name = record["level"].name.upper()
        severity_map = {
            "TRACE": SeverityNumber.TRACE,
            "DEBUG": SeverityNumber.DEBUG,
            "INFO": SeverityNumber.INFO,
            "SUCCESS": SeverityNumber.INFO,
            "WARNING": SeverityNumber.WARN,
            "ERROR": SeverityNumber.ERROR,
            "CRITICAL": SeverityNumber.FATAL,
        }
        severity_number = severity_map.get(level_name, SeverityNumber.INFO)
        log_record = LogRecord(
            timestamp=int(record["time"].timestamp() * 1e9),
            body=record["message"],
            severity_number=severity_number,
            severity_text=level_name,
            attributes={
                "logger.name": record.get("name", "app"),
                "logger.function": record.get("function", ""),
                "logger.line": record.get("line", 0),
                "request_id": record.get("extra", {}).get("request_id", ""),
            },
        )
        _otel_logger.emit(log_record)
    except Exception:
        pass


def init_telemetry(app: FastAPI | None = None) -> bool:
    """Initializes OpenTelemetry export to Grafana Cloud."""
    global _log_provider, _otel_logger

    if not settings.otel_configured:
        logger.debug("OpenTelemetry endpoint/headers not configured; skipping.")
        return False

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    headers = _parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS)
    service_name = settings.OTEL_SERVICE_NAME or settings.APP_NAME.lower()

    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": settings.APP_ENV,
    })

    # 1. Traces (APM)
    trace_endpoint = f"{endpoint}/v1/traces"
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=trace_endpoint, headers=headers)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # 2. Metrics (API latency, status codes, RAM & CPU)
    metric_endpoint = f"{endpoint}/v1/metrics"
    metric_exporter = OTLPMetricExporter(endpoint=metric_endpoint, headers=headers)
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=15000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # 3. System Metrics (RAM usage, CPU utilization via psutil)
    try:
        SystemMetricsInstrumentor().instrument()
    except Exception as exc:
        logger.debug("System metrics instrumentor deferred: {}", exc)

    # 4. Logs to Grafana Cloud
    log_endpoint = f"{endpoint}/v1/logs"
    _log_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=log_endpoint, headers=headers)
    _log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    _otel_logger = _log_provider.get_logger("divinlink.backend")

    # Hook Loguru to send logs to OpenTelemetry asynchronously
    logger.add(_loguru_to_otel_sink, level=settings.LOG_LEVEL.upper(), enqueue=True)

    # 5. FastAPI auto-instrumentation
    if app:
        try:
            FastAPIInstrumentor.instrument_app(
                app,
                tracer_provider=tracer_provider,
                meter_provider=meter_provider,
                excluded_urls="health,ping,docs,redoc,openapi.json",
            )
        except Exception as exc:
            logger.debug("FastAPI instrumentation notice: {}", exc)

    logger.info("OpenTelemetry connected to Grafana Cloud ({})", service_name)
    return True


def flush_telemetry() -> None:
    """Flushes any pending OpenTelemetry telemetry."""
    if _log_provider:
        with contextlib.suppress(Exception):
            _log_provider.force_flush(timeout_millis=5000)
