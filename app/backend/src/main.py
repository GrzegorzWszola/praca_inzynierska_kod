import os

from dotenv import load_dotenv
from fastapi import FastAPI
from backend.src.routers import books
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")

app = FastAPI(title="Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(books.router)

@app.get("/health")
def health():
    return {"status": "ok"}