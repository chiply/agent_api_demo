"""OpenTelemetry SDK initialization.

Reads standard OTEL_* environment variables for configuration:
- OTEL_SERVICE_NAME: service name (default: "agent-api-demo")
- OTEL_EXPORTER_OTLP_ENDPOINT: collector endpoint
- OTEL_SDK_DISABLED: set to "true" to disable the SDK entirely

The setup is resilient — if no collector is running, export errors are
silently ignored so the application continues to function normally.
"""

from __future__ import annotations

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    """Initialise OpenTelemetry TracerProvider, MeterProvider, and OTLP exporters.

    This function is safe to call even when no collector is available —
    export failures are logged but do not crash the application.
    """
    if os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true":
        logger.info("OpenTelemetry SDK disabled via OTEL_SDK_DISABLED")
        return

    service_name = os.environ.get("OTEL_SERVICE_NAME", "agent-api-demo")

    resource = Resource.create({"service.name": service_name})

    # --- Traces ---
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter()  # reads OTEL_EXPORTER_OTLP_* env vars
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    metric_exporter = OTLPMetricExporter()  # reads OTEL_EXPORTER_OTLP_* env vars
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    logger.info("OpenTelemetry SDK initialised for service %s", service_name)
