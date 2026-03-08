from fastapi import FastAPI

from app.routers.hello import router as hello_router

app = FastAPI()
app.include_router(hello_router)
