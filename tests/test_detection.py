import json
from pathlib import Path

import pytest

from stream_log_anamoly_detection.config import Settings
from stream_log_anamoly_detection.detection import AnomalyDetector
from stream_log_anamoly_detection.transform import transform

from .test_transform import VALID

MODEL = Path(Settings().model_path)


def _event(**overrides):
    return transform(json.dumps({**VALID, **overrides}))


@pytest.mark.skipif(not MODEL.is_file(), reason="model artifact not available")
def test_model_flags_attacks_and_not_routine_traffic():
    detector = AnomalyDetector(MODEL)
    routine = _event(severity="INFO", message="DNS query for github.com")
    attack = _event(severity="ERROR", message="Port scan detected from 185.114.141.41")
    scored = detector.score([routine, attack])
    assert [e.is_anomaly for e in scored] == [0, 1]
    assert scored[1].anomaly_score > scored[0].anomaly_score
    assert detector.score([]) == []
