from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def get_ready() -> JSONResponse:
    # When OTel SDK is disabled, always report ready
    if os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true":
        return JSONResponse(
            status_code=200,
            content=ReadyResponse(status="ready").model_dump(exclude_none=True),
        )

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(endpoint)
            # Any response means the collector is reachable
            return JSONResponse(
                status_code=200,
                content=ReadyResponse(status="ready").model_dump(exclude_none=True),
            )
    except Exception:
        logger.exception("OTel collector health check failed")
        return JSONResponse(
            status_code=503,
            content=ReadyResponse(
                status="not_ready",
                reason="OTel collector unreachable",
            ).model_dump(),
        )
