"""
app/services/pacs_handler.py
-----------------------------
Mock PACS (Picture Archiving and Communication System) handler.

When a scan is marked "Finished":
  1. Looks for a sample .dcm file in mock_pacs/samples/
  2. Uses pydicom to read its metadata (patient name, study date, modality)
  3. Returns a dict of extracted DICOM info for history logging
  4. Gracefully falls back if pydicom is not installed or no .dcm exists

This simulates image storage without needing real PACS infrastructure.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_BASE        = os.path.join(os.path.dirname(__file__), '..', '..', 'mock_pacs', 'samples')
_SAMPLE_DCM  = os.path.join(_BASE, 'sample.dcm')


def process_scan_completion(patient_name: str, exam_type: str, modality: str) -> dict:
    """
    Simulate PACS image ingestion when a scan is completed.

    Tries to read a sample .dcm file. If pydicom is unavailable or
    no file exists, returns a mocked response that is still useful
    for the history log.

    Returns a dict with:
        pacs_status   : 'ok' | 'fallback' | 'error'
        image_uid     : simulated SOP Instance UID
        modality      : the modality string
        study_date    : date string
        dicom_info    : dict of raw DICOM tags (if pydicom was used)
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    simulated_uid = f"1.2.840.{timestamp}.{abs(hash(patient_name)) % 99999}"

    try:
        import pydicom
        if os.path.exists(_SAMPLE_DCM):
            ds = pydicom.dcmread(_SAMPLE_DCM, stop_before_pixels=True)
            info = {
                'pacs_status': 'ok',
                'image_uid':   simulated_uid,
                'modality':    getattr(ds, 'Modality',    modality),
                'study_date':  getattr(ds, 'StudyDate',   timestamp[:8]),
                'dicom_info': {
                    'StudyDescription': getattr(ds, 'StudyDescription', exam_type),
                    'SOPClassUID':      str(getattr(ds, 'SOPClassUID', 'N/A')),
                    'Manufacturer':     getattr(ds, 'Manufacturer',    'SmartRAD Simulator'),
                }
            }
            logger.info(f"[PACS] ✅ DICOM read OK for {patient_name} | UID: {simulated_uid}")
            return info

        else:
            logger.warning(f"[PACS] No .dcm file found at {_SAMPLE_DCM} — using fallback.")

    except ImportError:
        logger.warning("[PACS] pydicom not installed — using simulated PACS response.")
    except Exception as e:
        logger.error(f"[PACS] Error reading DICOM: {e}")

    # ── Fallback (no pydicom / no file) ────────────────────────
    return {
        'pacs_status': 'fallback',
        'image_uid':   simulated_uid,
        'modality':    modality,
        'study_date':  timestamp[:8],
        'dicom_info': {
            'StudyDescription': exam_type,
            'SOPClassUID':      '1.2.840.10008.5.1.4.1.1.2',
            'Manufacturer':     'SmartRAD Simulator (Mock)',
        }
    }
