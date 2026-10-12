from ml_engine.config import Config
from sklearn.linear_model import Ridge
from ml_engine.baseline import MeanBaseline, MedianBaseline
from xgboost import XGBClassifier, XGBRegressor

class MlEngine:
    def __init__(self, config=None):
        self.model = None
        self.model_name = None
        self._is_fitted = False
        if config is not None:
            self.make_model(config)
        
    def make_model(self, config):
        self.model_name = config.model
        if config.model == "ridge":
            self.model = Ridge(**config.params)
        elif config.model == "mean_baseline":
            self.model = MeanBaseline(**config.params)
        elif config.model == "median_baseline":
            self.model = MedianBaseline(**config.params)
        elif config.model == "xgboost_reg":
            self.model = XGBRegressor(**config.params)
        elif config.model == "xgboost_tree":
            self.model = XGBRegressor()
        self._is_fitted = False

    def fit(self, X, y, sample_weight=None):
        if self.model is None:
            raise RuntimeError("No model set. Call make_model() first.")
        self.model.fit(X, y, sample_weight=sample_weight)
        self._is_fitted = True

    def predict(self, X):
        if self._is_fitted:
            return self.model.predict(X)

        raise RuntimeError("Fit model before prediction")


