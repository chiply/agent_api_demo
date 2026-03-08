from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.logging_config import setup_logging
from app.middleware import RequestLoggingMiddleware
from app.routers.hello import router as hello_router
from app.telemetry import setup_telemetry

setup_logging()
setup_telemetry()

app = FastAPI()
app.include_router(hello_router)
app.add_middleware(RequestLoggingMiddleware)

FastAPIInstrumentor.instrument_app(app)
