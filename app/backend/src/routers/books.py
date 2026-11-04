from datetime import timedelta
import logging
import os
import shutil
import uuid
from pathlib import Path

from book_parser.parser import BookParser
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import select, update
from backend.src.models.books_models import utcnow
from backend.src.routers.session import CookieDep
from backend.src.database import SessionDep, job_dir, set_status
from backend.src.models import Book
import httpx

logger = logging.getLogger()
load_dotenv()
NLP_URL = os.environ.get("NLP_URL", "http://nlp:8008")
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 50 * 1024 * 1024
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])

@router.post("/upload_epub", status_code=202)
async def upload_epub(file: UploadFile, tasks: BackgroundTasks, session: SessionDep, sid: CookieDep):
    if not (file.filename or "").lower().endswith(".epub"):
        logger.warning("Upload rejected – not an .epub file: %s", file.filename)
        raise HTTPException(400, ".epub file required")

    job_id = uuid.uuid4().hex
    d = job_dir(job_id)
    d.mkdir(parents=True)
    dest = d / "book.epub"

    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    logger.warning("Job %s: upload aborted – file exceeds %d MB limit", job_id, MAX_BYTES // (1024 * 1024))
                    raise HTTPException(413, "File size too big")
                out.write(chunk)
    except BaseException:
        shutil.rmtree(d, ignore_errors=True)
        raise

    logger.info("Job %s: epub uploaded (%.1f KB), queued for processing", job_id, size / 1024)
    book = Book(
        name=file.filename,
        job_id=job_id,
        browser_id=sid,
        status="queued"
    )
    try:
        session.add(book)
        session.commit()
    except Exception:
        session.rollback()
        shutil.rmtree(d, ignore_errors=True)
        raise
    session.refresh(book)
    tasks.add_task(process_job, job_id)
    return {"job_id": job_id}


@router.get("/{job_id}/status")
def job_status(job_id: str, session: SessionDep, sid: CookieDep):
    state = session.exec(select(Book.status).where(Book.job_id == job_id, Book.browser_id == sid)).first()
    if state is None:
        logger.warning("Status requested for unknown job: %s", job_id)
        raise HTTPException(404, "Unknown job")
    return {"status": state}

@router.get("/{job_id}/content") 
def get_content(job_id: str, session: SessionDep, sid: CookieDep):
    state = session.exec(select(Book.status).where(Book.job_id == job_id, Book.browser_id == sid)).first()
    if state is None:
        logger.warning("Content requested for unknown job: %s", job_id)
        raise HTTPException(404, "Unknown job")

    if state != "done":
        logger.warning("Job %s: content requested but status is '%s'", job_id, state)
        raise HTTPException(400, "Book is still processing")

    json_path = job_dir(job_id) / "book.json"
    if not json_path.is_file():
        logger.error("Job %s: status is 'done' but result file is missing", job_id)
        raise HTTPException(404, "Result not found")

    logger.info("Job %s: serving content", job_id)
    return FileResponse(
        json_path, 
        media_type="application/json", 
        filename=json_path.name
    )

@router.get("/mine")
def my_books(session: SessionDep, sid: CookieDep):
    session.exec(
        update(Book).where(Book.browser_id == sid).values(last_seen=utcnow())
    )
    session.commit()
    books = session.exec(
        select(Book).where(Book.browser_id == sid).order_by(Book.id.desc())
    ).all()
    return [{"job_id": b.job_id, "name": b.name, "status": b.status} for b in books]

@router.delete("/{job_id}", status_code=204)
def delete_book(job_id: str, session: SessionDep, sid: CookieDep):
    book = session.exec(
        select(Book).where(Book.job_id == job_id, Book.browser_id == sid)
    ).first()
    if book is None:
        raise HTTPException(404, "Unknown job")
    session.delete(book)
    session.commit()
    shutil.rmtree(job_dir(job_id), ignore_errors=True)

def run_vad(job_id: str, input_path: Path, output_path: Path):
    with httpx.Client(timeout=600) as client:
        with input_path.open("rb") as f:
            r = client.post(
                f"{NLP_URL}/prediction/{job_id}",
                files={"file": (input_path.name, f, "application/json")},
            )
        r.raise_for_status()
        output_path.write_bytes(r.content)

def process_job(job_id: str):
    d = job_dir(job_id)
    logger.info("Job %s: started processing", job_id)

    set_status(job_id, "parsing")
    try:
        BookParser().parse(d / "book.epub", d)
        parsed = next(p for p in d.glob("*.json") if p.name != "vad.json")
        parsed = parsed.rename(d / "book.json")
        logger.info("Job %s: parsing complete, starting VAD prediction", job_id)

        vad_out = d / "vad.json"
        set_status(job_id, "predicting")
        run_vad(job_id, parsed, vad_out)

        logger.info("Job %s: done", job_id)
        set_status(job_id, "done")
    except Exception:
        logger.exception("Job %s failed", job_id)
        set_status(job_id, "failed")

