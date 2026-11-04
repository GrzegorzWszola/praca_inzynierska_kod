from datetime import datetime, timezone
from enum import Enum
from sqlmodel import Field, SQLModel

def utcnow():
    return datetime.now(timezone.utc)

class BookStatus(str, Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    PREDICTING = "predicting"
    DONE = "done"
    FAILED = "failed"

class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    job_id: str = Field(unique=True, index=True)
    browser_id: str
    status: BookStatus = Field(default=BookStatus.QUEUED)
    created_at: datetime = Field(default_factory=utcnow)
    last_seen: datetime = Field(default_factory=utcnow, index=True)

class BookRead:
    pass

