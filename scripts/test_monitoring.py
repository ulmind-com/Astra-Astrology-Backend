"""Helper script to test Sentry and Grafana Cloud Loki connectivity."""

from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.sentry import init_sentry


def test_monitoring() -> None:
    setup_logging()
    print("--------------------------------------------------")
    print(f"App: {settings.APP_NAME} ({settings.APP_ENV})")
    print(f"Sentry Configured: {settings.sentry_configured}")
    print(f"Loki Configured:   {settings.loki_configured}")
    print("--------------------------------------------------")

    # 1. Test Sentry
    if settings.sentry_configured:
        print("Testing Sentry error capture...")
        import sentry_sdk

        init_sentry()
        sentry_sdk.capture_message("Hello from Astra Astrology - Sentry connection verified!")
        print("✅ Sentry test message dispatched! Check your Sentry Issues tab.")
    else:
        print("⚠️ SENTRY_DSN is not set in environment or .env file.")

    # 2. Test Loki
    if settings.loki_configured:
        print("Testing Grafana Loki log push...")
        logger.info("Hello from Astra Astrology - Grafana Loki logging verified!")
        print("✅ Loki test log dispatched! Check your Grafana Cloud Explore tab.")
    else:
        print("⚠️ GRAFANA_LOKI_* is not set in environment or .env file.")

    print("--------------------------------------------------")


if __name__ == "__main__":
    test_monitoring()
