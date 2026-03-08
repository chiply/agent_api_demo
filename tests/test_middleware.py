"""Tests for request logging middleware."""
import json
import logging

from app.logging_config import JSONFormatter


async def test_request_logging_middleware_logs_request(client, caplog):
    """Middleware should log method, route, status_code, duration_ms."""
    with caplog.at_level(logging.INFO, logger="app.middleware"):
        response = await client.get("/hello")
    assert response.status_code == 200
    # Find the log record from our middleware
    middleware_records = [
        r for r in caplog.records if r.name == "app.middleware"
    ]
    assert len(middleware_records) >= 1
    record = middleware_records[0]
    assert hasattr(record, "method")
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert hasattr(record, "status_code")
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert hasattr(record, "duration_ms")
    assert isinstance(record.duration_ms, float)  # type: ignore[attr-defined]


async def test_request_logging_middleware_json_output(client):
    """When formatted with JSONFormatter, request log includes all fields."""
    formatter = JSONFormatter(service_name="test-service")
    handler = logging.Handler()
    handler.setFormatter(formatter)

    logger = logging.getLogger("app.middleware")
    logger.addHandler(handler)
    captured = []
    original_emit = handler.emit

    def capture_emit(record):
        captured.append(formatter.format(record))

    handler.emit = capture_emit  # type: ignore[assignment]

    try:
        await client.get("/hello")
    finally:
        logger.removeHandler(handler)

    assert len(captured) >= 1
    parsed = json.loads(captured[0])
    assert parsed["method"] == "GET"
    assert parsed["status_code"] == 200
    assert "duration_ms" in parsed
    assert "path" in parsed
