from fastapi import FastAPI 
from webhooks.example.router import router as example_router

webhooks_app = FastAPI()

def startup_stream():
    pass

webhooks_app.include_router(example_router, tags=["example"], prefix="/example")
