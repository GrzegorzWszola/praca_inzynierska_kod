from datetime import timedelta
import os
from pathlib import Path
import shutil
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, update
from sqlmodel import SQLModel, Session, select

from backend.src.models.books_models import Book, utcnow

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "database.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

def job_dir(job_id: str) -> Path:
    return DATA_DIR / job_id

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def cleanup(day_number: int):
    with Session(engine) as session:
        books = session.exec(select(Book).where(Book.last_seen < utcnow() - timedelta(days=day_number))).all()
        if not books:
            return

        for book in books:
            shutil.rmtree(job_dir(book.job_id), ignore_errors=True)
            session.delete(book)
        
        session.commit()


def set_status(job_id: str, status: str):
    with Session(engine) as s:
        s.exec(update(Book).where(Book.job_id == job_id).values(status=status))
        s.commit()

SessionDep = Annotated[Session, Depends(get_session)]
