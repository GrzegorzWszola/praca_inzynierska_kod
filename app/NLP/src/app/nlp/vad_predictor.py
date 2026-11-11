import json
import logging
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

lexicon = {
    "joy": [0.96, 0.684, 0.588],
    "sadness": [-0.896, -0.424, -0.672],
    "tense": [-0.392, 0.620, 0.058],
    "calm": [0.75, -0.9, -0.373],
}

class VADPredictor:
    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load_model(self, input_path: Path):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = input_path.name

        self.tokenizer = AutoTokenizer.from_pretrained(input_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            input_path,
            dtype=torch.float32,
        )
        
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model '%s' loaded on %s", self.model_name, self.device)

    def fit_model_space(self, pred, lex_ref, lo=5, hi=95, shrink=1.0):
        center = np.median(pred, axis=0)
        s_pred = np.percentile(pred, hi, axis=0) - np.percentile(pred, lo, axis=0)
        s_lex  = np.percentile(lex_ref, hi, axis=0) - np.percentile(lex_ref, lo, axis=0)
        k = (s_pred / s_lex) * shrink
        return center, k

    def fit_centroids(self, cents_lex, center, k):
        return {name: center + np.asarray(c) * k for name, c in cents_lex.items()}

    def fit_neutral_radius(self, pred, center, pct=25, axis_w=(1, 1, 0)):
        w = np.asarray(axis_w)
        r = np.linalg.norm((pred - center) * w, axis=1)
        return np.percentile(r, pct)

    def predict_vad(self, texts: list[str], batch_size: int = 32, max_length: int = 256):
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.inference_mode():
                logits = self.model(**inputs).logits
            results.extend(logits.cpu().tolist())
        return results

    def process_data(self, data: dict) -> dict:
        items = []
        for ch in data["chapters"]:
            for p in ch["paragraphs"]:
                for s in p["sentences"]:
                    items.append((s["id"], s["text"]))

        ids = [i for i, _ in items]
        texts = [t for _, t in items]

        logger.info("Running inference on %d sentences across %d chapters", len(texts), len(data["chapters"]))
        preds = self.predict_vad(texts)

        logger.info("Calculating new centroids values for emotions range from predictions")
        lex_ref_array = np.array(list(lexicon.values()))
        center, k = self.fit_model_space(preds, lex_ref_array)
        cents = self.fit_centroids(lexicon, center, k)

        logger.info("Calculating neutral circle around the central point")
        r_neutral = self.fit_neutral_radius(preds, center)

        vad = {
            sid: [round(v, 4), round(a, 4), round(d, 4)]
            for sid, (v, a, d) in zip(ids, preds)
        }

        safe_centroids = {
            name: [round(float(val), 4) for val in vec] 
            for name, vec in cents.items()
            if name != "neutral"
        }
        safe_r_neutral = round(float(r_neutral), 4)

        return {
            "meta": {
                "model_name": self.model_name,
                "columns": ["valence", "arousal", "dominance"],
                "config": {
                    "centroids": safe_centroids,
                    "r_neutral": safe_r_neutral,
                    "k": [round(float(x), 4) for x in k],
                    "center": [round(float(x), 4) for x in center]
                }
            },
            "vad": vad,
        }



