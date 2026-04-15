from sklearn.ensemble import IsolationForest
import numpy as np
import logging

logger = logging.getLogger("AnomalyModel")

class StreamingAnomalyDetector:
    def __init__(self, n_estimators=100, contamination=0.05, window_size=100, min_fit_size=50):
        self.model = IsolationForest(
            n_estimators=n_estimators, 
            contamination=contamination, 
            random_state=42
        )
        self.window_size = window_size
        self.min_fit_size = min_fit_size
        self.recent_data = []
        logger.info(f"Initialized IsolationForest (window_size={self.window_size}, min_fit_size={self.min_fit_size})")

    def process_and_predict(self, amount: float) -> bool:
        """
        Takes a new transaction amount, updates the sliding window, 
        fits the model if enough data, and returns True if anomalous.
        """
        self.recent_data.append([amount])
        
        if len(self.recent_data) > self.window_size:
            self.recent_data.pop(0)
            
        if len(self.recent_data) >= self.min_fit_size:
            # We fit dynamically. In production, this might be a background task or periodic refit.
            self.model.fit(self.recent_data)
            prediction = self.model.predict([[amount]])[0]
            # -1 means anomaly, 1 means normal
            return bool(prediction == -1)
            
        # Not enough data to predict yet
        return False
