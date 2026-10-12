AVAIBLE_MODELS = [
    "ridge", "mean_baseline", "median_baseline", "xgboost_reg", "xgboost_tree", "deberta_vad"
]

class Config:
    def __init__(self, model: str, params: dict | None = None):
        if model not in AVAIBLE_MODELS:
            raise ValueError(f"Model is not avaible: {model}")
        self.model = model
        self.params = params or {}

class PreMadeConfigs:
    def xgboost():
        return Config(
            model="xgboost_reg",
            params={
                "n_estimators": 3000,
                "learning_rate": 0.03,
                "max_depth": 6,
                "min_child_weight": 5,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "reg_lambda": 1.0,
                "reg_alpha": 0.0,
                "gamma": 0.0,
                "tree_method": "hist",
                "n_jobs": 4,
                "random_state": 42
            }
        )

    def xgboost_tree():
        return Config(
            model="xgboost_tree",
            params={
                "booster": "gbtree",
                "tree_method": "hist",
                "colsample_bytree": 0.3,
                "max_depth": 4,
                "learning_rate": 0.03,
                "min_child_weight": 6,
                "subsample": 0.8,
                "objective": "reg:pseudohubererror",
                "n_estimators": 3000,
                "reg_lambda": 5.0,
                "reg_alpha": 0.0,
                "gamma": 0.0,
                "eval_metric": "mae",
                "n_jobs": 4,
                "random_state": 42
            }
        )

    def ridge():
        return Config(
            model="ridge",
            params={
                "alpha": 0.1
            }
        )

    def median_baseline():
        return Config(
            model="median_baseline",
            params={}
        )

    def mean_baseline():
        return Config(
            model="mean_baseline",
            params={}
        )
