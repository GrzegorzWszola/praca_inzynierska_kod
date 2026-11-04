import asyncio
from contextlib import asynccontextmanager
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from backend.src.database import cleanup, create_db_and_tables
from backend.src.routers import books, session
from fastapi.middleware.cors import CORSMiddleware

async def periodic_cleanup(day_number: int, interval_seconds: int = 3600):
    while True:
        try:
            cleanup(day_number)
        except Exception:
            pass
        
        await asyncio.sleep(interval_seconds)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    cleanup_task = asyncio.create_task(periodic_cleanup(day_number=3, interval_seconds=3600))
    
    yield
    
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

load_dotenv()
origins = os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")

app = FastAPI(title="Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(books.router)
app.include_router(session.router)

@app.get("/health")
def health():
    return {"status": "ok"}