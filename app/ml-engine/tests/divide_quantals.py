import json
import numpy as np

preds = np.load("reports/preds_test.npy")

print(f"V: {np.max(preds[:, 0])}")
print(f"A: {np.max(preds[:, 1])}")
print(f"V: {np.min(preds[:, 0])}")
print(f"A: {np.min(preds[:, 1])}")
exit(0)

np_v = np.arange(0.05, 1.0, 0.05).tolist()
np_a = np.arange(0.1, 1.0, 0.1).tolist()

v_quantiles = [round(k, 2) for k in np_v]
a_quantiles = [round(k, 2) for k in np_a]

print(v_quantiles)
print(len(v_quantiles))
print(a_quantiles)
print(len(a_quantiles))

centroids = {
    
}

config = {
    "global": {    
        "source": "cr4_narr test, predictions of deberta-vad-seed42",
        "n_samples": int(len(preds)),
        "v_edges": [round(float(x), 4) for x in np.quantile(preds[:, 0], v_quantiles)],
        "a_edges": [round(float(x), 4) for x in np.quantile(preds[:, 1], a_quantiles)],
    },
    "per_book": {
        "enabled": True,
        "v_quantiles": v_quantiles,
        "a_quantiles": a_quantiles
    }
}

with open("quantization.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)