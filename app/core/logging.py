"""Loguru based logging setup, with uvicorn/stdlib logs routed through it."""

import logging
import sys

from loguru import logger

from app.core.config import settings


class _InterceptHandler(logging.Handler):
    """Redirects stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
        enqueue=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "pymongo"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = [_InterceptHandler()]
        std_logger.propagate = False
