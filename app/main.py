from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.routers.hello import router as hello_router
from app.telemetry import setup_telemetry

setup_telemetry()

app = FastAPI()
app.include_router(hello_router)

FastAPIInstrumentor.instrument_app(app)
