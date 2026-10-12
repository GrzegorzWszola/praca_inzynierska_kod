import numpy as np


class MeanBaseline:
    """
    Baseline estimator that predicts the mean of the training targets.

    Implements a scikit-learn compatible interface (fit/predict).
    """

    def fit(self, X, y, sample_weight=None):
        """
        Fit the baseline model by computing the weighted mean of training targets.

        Args:
            X: Training input features (unused, accepted for API consistency).
            y: Target values of shape (n_samples,) or (n_samples, n_targets).
            sample_weight: Optional array of sample weights for computing weighted mean.

        Returns:
            self: The fitted estimator instance.
        """
        self.mean_ = np.average(y, axis=0, weights=sample_weight)
        return self

    def predict(self, X):
        """
        Predict constant mean values for all samples in X.

        Args:
            X: Input samples of shape (n_samples, n_features) or sequence of length n_samples.

        Returns:
            np.ndarray: Predicted array of shape (n_samples, n_targets) repeating the learned mean.
        """
        return np.tile(self.mean_, (len(X), 1))


class MedianBaseline:
    """
    Baseline estimator that predicts the median of the training targets.

    Implements a scikit-learn compatible interface (fit/predict).
    """

    def fit(self, X, y, sample_weight=None):
        """
        Fit the baseline model by computing the median of training targets.

        Args:
            X: Training input features (unused, accepted for API consistency).
            y: Target values of shape (n_samples,) or (n_samples, n_targets).
            sample_weight: Unused, accepted for scikit-learn API compatibility.

        Returns:
            self: The fitted estimator instance.
        """
        self.median_ = np.median(y, axis=0)
        return self

    def predict(self, X):
        """
        Predict constant median values for all samples in X.

        Args:
            X: Input samples of shape (n_samples, n_features) or sequence of length n_samples.

        Returns:
            np.ndarray: Predicted array of shape (n_samples, n_targets) repeating the learned median.
        """
        return np.tile(self.median_, (len(X), 1))