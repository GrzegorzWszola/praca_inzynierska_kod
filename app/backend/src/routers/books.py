import logging
import os
import shutil
import uuid
from pathlib import Path

from book_parser.parser import BookParser
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
import httpx

logger = logging.getLogger()
load_dotenv()
NLP_URL = os.environ.get("NLP_URL", "http://nlp:8008")
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 50 * 1024 * 1024
logger = logging.getLogger(__name__)

# Temporary solution
JOBS: dict[str, dict] = {}

router = APIRouter(prefix="/books", tags=["books"])

def job_dir(job_id: str) -> Path:
    return DATA_DIR / job_id

@router.post("/upload_epub", status_code=202)
async def upload_epub(file: UploadFile, tasks: BackgroundTasks):
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
    JOBS[job_id] = {"status": "queued"}
    tasks.add_task(process_job, job_id)
    return {"job_id": job_id}


@router.get("/{job_id}/status")
def job_status(job_id: str):
    state = JOBS.get(job_id)
    if state is None:
        logger.warning("Status requested for unknown job: %s", job_id)
        raise HTTPException(404, "Unknown job")
    return state

@router.get("/{job_id}/content") 
def get_content(job_id: str):
    state = JOBS.get(job_id)
    if state is None:
        logger.warning("Content requested for unknown job: %s", job_id)
        raise HTTPException(404, "Unknown job")

    if state.get("status") != "done":
        logger.warning("Job %s: content requested but status is '%s'", job_id, state.get("status"))
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
    JOBS[job_id] = {"status": "parsing"}
    try:
        BookParser().parse(d / "book.epub", d)
        parsed = next(p for p in d.glob("*.json") if p.name != "vad.json")
        parsed = parsed.rename(d / "book.json")
        logger.info("Job %s: parsing complete, starting VAD prediction", job_id)

        vad_out = d / "vad.json"
        JOBS[job_id] = {"status": "predicting"}
        run_vad(job_id, parsed, vad_out)

        logger.info("Job %s: done", job_id)
        JOBS[job_id] = {"status": "done", "book_id": job_id}
    except Exception:
        logger.exception("Job %s failed", job_id)
        JOBS[job_id] = {"status": "error", "detail": "Processing failed"}