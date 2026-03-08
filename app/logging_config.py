"""Structured JSON logging configuration with OTel trace correlation."""
from __future__ import annotations

import json
import logging
import os
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Minimal JSON log formatter with OpenTelemetry trace correlation."""

    def __init__(self, service_name: str = "agent-api-demo") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "otelTraceID", ""),
            "span_id": getattr(record, "otelSpanID", ""),
            "service.name": self.service_name,
        }

        # Include extra fields set on the record (e.g. from middleware)
        for key in ("method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure root logger with JSON formatting and per-module overrides."""
    service_name = os.environ.get("OTEL_SERVICE_NAME", "agent-api-demo")
    root_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(root_level)

    # Remove existing handlers to avoid duplicate output
    # but only StreamHandlers we'd be replacing
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter(service_name=service_name))
    root_logger.addHandler(handler)

    # Per-module log level overrides: LOG_LEVEL_<dotted.module>=<LEVEL>
    prefix = "LOG_LEVEL_"
    for key, value in os.environ.items():
        if key.startswith(prefix) and key != "LOG_LEVEL":
            module_name = key[len(prefix):]
            # Support both LOG_LEVEL_app.routers and LOG_LEVEL_app_routers
            # but prefer dots (env vars with dots work in .env files)
            level = value.upper()
            if hasattr(logging, level):
                logging.getLogger(module_name).setLevel(getattr(logging, level))
