import json
import logging
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

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

    def load_quantization(self, input_path: Path):
        cfg = json.loads(Path(input_path).read_text(encoding="utf-8"))
        self.global_quantize_config = cfg["global"]
        self.per_book_quantize_config = cfg["per_book"]
        logger.info("Quantization config loaded from %s", input_path.name)

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

        vad = {
            sid: [round(v, 4), round(a, 4), round(d, 4)]
            for sid, (v, a, d) in zip(ids, preds)
        }

        quantize_configs = {"global": self.global_quantize_config}
        if self.per_book_quantize_config.get("enabled"):
            v = np.array([p[0] for p in preds])
            a = np.array([p[1] for p in preds])
            quantize_configs["per_book"] = {
                "n_samples": len(v),
                "v_edges": np.quantile(v, self.per_book_quantize_config["v_quantiles"]).round(4).tolist(),
                "a_edges": np.quantile(a, self.per_book_quantize_config["a_quantiles"]).round(4).tolist(),
                "mean": {
                    "valence": round(float(v.mean()), 4),
                    "arousal": round(float(a.mean()), 4),
                },
                "std": {
                    "valence": round(float(v.std()), 4),
                    "arousal": round(float(a.std()), 4),
                },
            }

        return {
            "meta": {
                "model_name": self.model_name,
                "columns": ["valence", "arousal", "dominance"],
                "quantize_configs": quantize_configs,
            },
            "vad": vad,
        }



