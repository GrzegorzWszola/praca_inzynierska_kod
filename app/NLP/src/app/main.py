from fastapi import FastAPI

from src.app.routers import prediction

app = FastAPI(title="NLP")

app.include_router(prediction.router)
