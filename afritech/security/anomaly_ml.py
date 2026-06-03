import logging
import os
import joblib
import numpy as np

from sklearn.ensemble import IsolationForest


logger = logging.getLogger(__name__)

# =====================================================
# ✅ CONFIG
# =====================================================

MODEL_PATH = "models/anomaly_model.pkl"
CONTAMINATION = 0.05


# =====================================================
# ✅ MODEL INSTANCE
# =====================================================

MODEL = None


# =====================================================
# ✅ INITIALIZATION
# =====================================================

def init_model():
    """
    Initialize model (load or create new).
    """
    global MODEL

    if os.path.exists(MODEL_PATH):
        try:
            MODEL = joblib.load(MODEL_PATH)
            logger.info("[ML] Model loaded successfully")
        except Exception as e:
            logger.error(f"[ML] Failed to load model: {e}")
            MODEL = _create_model()
    else:
        MODEL = _create_model()


def _create_model():
    """
    Create a new IsolationForest model.
    """
    logger.info("[ML] Creating new IsolationForest model")

    return IsolationForest(
        contamination=CONTAMINATION,
        random_state=42,
        n_estimators=100,
    )


# =====================================================
# ✅ TRAINING
# =====================================================

def train_model(data: list):
    """
    Train model with dataset.

    data = [
        [requests, latency, failures],
        ...
    ]
    """
    global MODEL

    try:
        if not data or len(data) < 10:
            raise ValueError("Not enough training data")

        X = np.array(data)

        MODEL = _create_model()
        MODEL.fit(X)

        # ✅ Save model
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(MODEL, MODEL_PATH)

        logger.info(f"[ML] Model trained and saved ({len(data)} samples)")

    except Exception as e:
        logger.exception("[ML] Training failed")
        raise


# =====================================================
# ✅ SINGLE PREDICTION
# =====================================================

def predict_anomaly(features: list) -> bool:
    """
    Predict anomaly for a single feature set.

    features = [requests, latency, failures]
    """
    global MODEL

    try:
        if MODEL is None:
            logger.warning("[ML] Model not initialized")
            return False

        if len(features) != 3:
            raise ValueError("Features must be [requests, latency, failures]")

        X = np.array([features])

        result = MODEL.predict(X)

        # -1 = anomaly, 1 = normal
        return result[0] == -1

    except Exception as e:
        logger.error(f"[ML] Prediction error: {e}")
        return False


# =====================================================
# ✅ BATCH PREDICTION
# =====================================================

def predict_batch(data: list) -> list:
    """
    Predict anomalies for multiple samples.

    Returns list of booleans.
    """
    global MODEL

    try:
        if MODEL is None:
            raise RuntimeError("Model not initialized")

        X = np.array(data)

        results = MODEL.predict(X)

        return [r == -1 for r in results]

    except Exception as e:
        logger.error(f"[ML] Batch prediction failed: {e}")
        return []


# =====================================================
# ✅ SCORE (ADVANCED)
# =====================================================

def anomaly_score(features: list) -> float:
    """
    Return anomaly score (lower = more anomalous).
    """
    global MODEL

    try:
        if MODEL is None:
            return 0.0

        X = np.array([features])

        score = MODEL.decision_function(X)

        return float(score[0])

    except Exception:
        return 0.0
