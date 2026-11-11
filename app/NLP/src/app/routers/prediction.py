import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, File, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse
from src.app.nlp.vad_predictor import VADPredictor

logger = logging.getLogger(__name__)

load_dotenv()
MODEL_PATH = Path(os.getenv("MODEL_PATH"))

logger.info("Loading VAD model from %s", MODEL_PATH)
model = VADPredictor()
model.load_model(MODEL_PATH)
logger.info("VAD model ready (device: %s)", model.device)

router = APIRouter(prefix="/prediction", tags=["prediction"])

@router.post("/{job_id}", status_code=200)
async def predict_vad(job_id: str, file: UploadFile):
    data = json.loads(await file.read())
    logger.info("Job %s: starting VAD prediction", job_id)
    out = await run_in_threadpool(model.process_data, data)
    logger.info("Job %s: prediction done (%d sentences)", job_id, len(out.get("vad", {})))

    payload = json.dumps(out, ensure_ascii=False).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="vad.json"'},
    )
