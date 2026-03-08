"""Tests for structured JSON logging configuration."""
import json
import logging
import os

from app.logging_config import JSONFormatter, setup_logging


def test_json_formatter_outputs_valid_json():
    formatter = JSONFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert "timestamp" in parsed
    assert "service.name" in parsed
    assert parsed["service.name"] == "test-service"


def test_json_formatter_includes_trace_fields():
    formatter = JSONFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="traced",
        args=(),
        exc_info=None,
    )
    # Simulate OTel injected attributes
    record.otelTraceID = "abc123"  # type: ignore[attr-defined]
    record.otelSpanID = "def456"  # type: ignore[attr-defined]
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["trace_id"] == "abc123"
    assert parsed["span_id"] == "def456"


def test_json_formatter_handles_missing_trace_fields():
    formatter = JSONFormatter(service_name="test-service")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="no trace",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["trace_id"] == ""
    assert parsed["span_id"] == ""


def test_setup_logging_configures_root_logger():
    setup_logging()
    root = logging.getLogger()
    # Should have at least one handler with JSONFormatter
    json_handlers = [
        h for h in root.handlers if isinstance(h.formatter, JSONFormatter)
    ]
    assert len(json_handlers) >= 1


def test_per_module_log_level_override(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL_app.routers", "DEBUG")
    setup_logging()
    logger = logging.getLogger("app.routers")
    assert logger.level == logging.DEBUG


def test_json_formatter_handles_exception():
    formatter = JSONFormatter(service_name="test-service")
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="error occurred",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "exception" in parsed
    assert "ValueError: boom" in parsed["exception"]
