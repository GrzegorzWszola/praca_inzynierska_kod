import json
import numpy as np

preds = np.load("reports/preds_test.npy")

config = {
    "global": {    
        "source": "cr4_narr test, predictions of deberta-vad-seed42",
        "n_samples": int(len(preds)),
        "v_edges": [round(float(x), 4) for x in np.quantile(preds[:, 0], [0.25, 0.5, 0.75])],
        "a_edges": [round(float(x), 4) for x in np.quantile(preds[:, 1], [0.5])],
    },
    "per_book": {
        "enabled": True,
        "v_quantiles": [0.25, 0.5, 0.75],
        "a_quantiles": [0.5]
    }
}

with open("quantization.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)