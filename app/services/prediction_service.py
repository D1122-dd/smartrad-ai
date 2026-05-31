import joblib
import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
_BASE = os.path.dirname(__file__)
_MODEL_PATH = os.path.join(_BASE, '..', 'ml', 'smartrad_rfR_model.pkl')
_ENC_PATH   = os.path.join(_BASE, '..', 'ml', 'label_encoders.pkl')

# ── Load once at module-import (Startup) ──────────────────────────────────────
_model = None
_encoders = {}

def load_model():
    """Explicitly (re)load the model into memory."""
    global _model, _encoders
    try:
        if os.path.exists(_MODEL_PATH):
            _model = joblib.load(_MODEL_PATH)
            logger.info("SmartRAD AI model (v2) loaded successfully.")
        else:
            logger.warning(f"AI model file not found at {_MODEL_PATH}")

        if os.path.exists(_ENC_PATH):
            _encoders = joblib.load(_ENC_PATH)
            logger.info("Label encoders loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load AI model/encoders: {e}")
        _model = None

# Trigger load on first import
load_model()

# ── Feature metadata (mirrors training script) ────────────────────────────────
# Categorical features that were label-encoded during training
CATEGORICAL_FEATURES = ['exam_type', 'modality_type', 'patient_age_group', 'body_part']

# Base duration by exam type (mirrors training script logic)
EXAM_BASE_MAP = {'Chest':8, 'Knee':12, 'Spine':18, 'Abdomen':15, 'Hand':7, 'Pelvis':14, 'Shoulder':13}

# Feature order must match training exactly
FEATURE_ORDER = [
    'exam_type',
    'modality_type',
    'request_hour',
    'day_of_week',
    'is_urgent',
    'room_load_at_request',
    'technician_experience',
    'patient_age_group',
    'body_part',
    'base_duration'
]

# Allowed values (from dataset script)
VALID_EXAM_TYPES    = ['Chest', 'Knee', 'Spine', 'Abdomen', 'Hand', 'Pelvis', 'Shoulder']
VALID_MODALITIES    = ['DX', 'CR']
VALID_AGE_GROUPS    = ['Child', 'Adult', 'Elderly']
VALID_BODY_PARTS    = ['Thorax', 'Lower_Limb', 'Spine', 'Abdomen', 'Upper_Limb']

# Default fallbacks for missing optional fields
_DEFAULTS = {
    'request_hour':          8,
    'day_of_week':           0,
    'room_load_at_request':  5,
    'technician_experience': 5,
}


def predict_duration(exam_type, modality_type, patient_age_group, body_part,
                     is_urgent=0, request_hour=None, day_of_week=None,
                     room_load_at_request=None, technician_experience=None):
    """
    Predict estimated scan duration in minutes.
    """
    if _model is None:
        # Fallback: rule-based estimate when model not available
        est = EXAM_BASE_MAP.get(exam_type, 12) + (3 if not is_urgent else -2)
        return int(est), 'fallback'

    try:
        # Fill optional fields with defaults
        rh  = request_hour          if request_hour          is not None else datetime.now().hour
        dow = day_of_week           if day_of_week           is not None else datetime.now().weekday()
        rl  = room_load_at_request  if room_load_at_request  is not None else _DEFAULTS['room_load_at_request']
        te  = technician_experience if technician_experience is not None else _DEFAULTS['technician_experience']
        bd  = EXAM_BASE_MAP.get(exam_type, 12)

        # Build a temporary DataFrame to handle encoding safely (matching user inference logic)
        data = {
            'exam_type': [exam_type],
            'modality_type': [modality_type],
            'request_hour': [rh],
            'day_of_week': [dow],
            'is_urgent': [int(is_urgent)],
            'room_load_at_request': [rl],
            'technician_experience': [te],
            'patient_age_group': [patient_age_group],
            'body_part': [body_part],
            'base_duration': [bd]
        }
        df = pd.DataFrame(data)

        # Apply Label Encoding
        for col in _encoders.keys():
            if col in df.columns:
                try:
                    df[col] = _encoders[col].transform(df[col].astype(str))
                except:
                    # Fallback for unseen labels
                    df[col] = 0

        # Ensure correct feature order
        df = df[FEATURE_ORDER]

        prediction = _model.predict(df)[0]
        duration   = int(np.clip(prediction, 4, 55))
        return duration, 'ok'

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return 15, 'error'


def get_model_info():
    """Return basic info about the loaded model (for debugging / admin pages)."""
    if _model is None:
        return {'status': 'not_loaded'}
    info = {
        'status':    'loaded',
        'type':      type(_model).__name__,
        'features':  FEATURE_ORDER,
        'n_estimators': getattr(_model, 'n_estimators', 'N/A'),
        'max_depth':    getattr(_model, 'max_depth',    'N/A'),
    }
    return info
