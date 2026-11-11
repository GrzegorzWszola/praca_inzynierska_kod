from collections import defaultdict
import json
import logging
import math
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from backend.src.models.books_models import Book
from backend.src.database import SessionDep, job_dir
from backend.src.routers.session import CookieDep

class PredictionRequest(BaseModel):
    sentence_ids: list[int]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])

@router.post("/{job_id}")
def predict_value(job_id: str, session: SessionDep, sid: CookieDep, body: PredictionRequest):
    book = session.exec(select(Book).where(Book.job_id == job_id, Book.browser_id == sid))
    if book is None:
        logger.warning("Prediction requested for unknown book: %s", job_id)
        raise HTTPException(404, "Unknown book")

    sentence_ids = body.sentence_ids
    if not sentence_ids:
        logger.warning("Empty list for book: %s", job_id)
        raise HTTPException(404, "Empty list")

    top, p1, margin = predict_value(sentence_ids, job_id)

    return {
        "job_id": job_id,
        "label": top,
        "certainty": p1,
        "margin": margin
    }

def predict_value(sentences: list[int], job_id: str):
    d = job_dir(job_id) / "vad.json"

    vad_file = json.loads(d.read_text())
    config = vad_file["meta"]["config"]
    vad_values = vad_file["vad"]

    vad_values = {
        k: v for k, v in vad_values.items() 
        if min(sentences) <= int(k) <= max(sentences)
    }

    labels, label_count = assign_labels(vad_values, config["centroids"], config["center"], config["r_neutral"])
    top, p1, margin = decide_label(label_count)

    return top, p1, margin

def assign_labels(values: dict, centroids: dict, center, r_neutral) -> dict:
    if not values: return {}, {}
    labels = {}
    for sentence_id, vad in values.items():

        if euclidean_distance(vad, center) < r_neutral:
            labels[sentence_id] = "neutral"
            continue

        best_name = None
        best_distance = float("inf")
        for name, centroid in centroids.items():
            d = euclidean_distance(vad, centroid)
            if d < best_distance:
                best_distance = d
                best_name = name

        labels[sentence_id] = best_name

    num_of_labels = len(labels)
    label_count = {}
    for label in labels.values():
        label_count[label] = label_count.get(label, 0) + 1

    for label, value in label_count.items():
        label_count[label] = value / num_of_labels

    return labels, label_count

def decide_label(label_count: dict):
    ranked = sorted(label_count.items(), key=lambda x: x[1], reverse=True)
    top, p1 = ranked[0]
    p2 = ranked[1][1] if len(ranked) > 1 else 0.0
    return top, p1, round(p1 - p2, 4)
        
def euclidean_distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


