"""Message anomaly detector: scores log lines with the pre-trained RandomForest from anamoly_detection_ml.

The model was pickled from a notebook, so it refers to `MsgFeatures` / `MessageDetector` and the helper
functions by name. The definitions below must stay identical to anamoly_detection_ml/detect_anomaly.py.
"""

import dataclasses
import logging
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..transform import SecurityEvent

log = logging.getLogger(__name__)

SEV_MAP = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
SEV_RE = re.compile(r"^(INFO|WARNING|ERROR|CRITICAL)\s+")
IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
USER_PREFIX_RE = re.compile(r"^(Accepted login for|Session closed for|Failed password for|sudo session opened for|VPN login for) (\S+)")
ALL_COLS = ["sev_ord", "rarity", "log_size_mb", "n_ext_ip"] + [f"text_svd_{i}" for i in range(6)]


def to_template(msg: str) -> str:
    t = IP_RE.sub("<IP>", msg)
    t = USER_PREFIX_RE.sub(r"\1 <USER>", t)
    t = re.sub(r"^\w+ (logged in from)", r"<USER> \1", t)
    t = re.sub(r"\b(from|after) [A-Z]{2}\b", r"\1 <CC>", t)
    t = re.sub(r"files-\d+", "files-<N>", t)
    t = re.sub(r"doc\d+\.docx", "doc<N>.docx", t)
    t = re.sub(r"HTTP/\d\.\d", "HTTP/<V>", t)
    t = re.sub(r"\bport \d+", "port <PORT>", t)
    t = re.sub(r"(\bof )\d+( [MK]B)", r"\1<N>\2", t)
    t = re.sub(r"(<IP>):\d+$", r"\1:<PORT>", t)
    return t


def parse_message(msg: str):
    ips = IP_RE.findall(msg)
    size = re.search(r"of (\d+) ([MK])B", msg)
    size_mb = int(size.group(1)) * (1.0 if size.group(2) == "M" else 1 / 1024) if size else 0.0
    n_ext = sum(not ip.startswith(("10.", "192.168.")) for ip in ips)
    user = USER_PREFIX_RE.match(msg)
    entity = ips[0] if ips else (user.group(2) if user else "")
    return size_mb, n_ext, entity


def strip_severity(line: pd.Series) -> pd.Series:
    return line.str.replace(SEV_RE, "", regex=True)


class MsgFeatures:
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        msg = strip_severity(df.line)
        tpl = msg.map(to_template)
        parsed = np.array([parse_message(m)[:2] for m in msg]).reshape(-1, 2)
        F = pd.DataFrame(index=df.index)
        F["sev_ord"] = df.type.map(SEV_MAP).fillna(0).values
        F["rarity"] = -np.log((tpl.map(self.tpl_counts_).fillna(0).values + 1) / (self.n_ref_ + 1))
        F["log_size_mb"], F["n_ext_ip"] = np.log1p(parsed[:, 0]), parsed[:, 1]
        svd = self.svd_.transform(self.tfidf_.transform(tpl))
        for i in range(svd.shape[1]):
            F[f"text_svd_{i}"] = svd[:, i]
        return F


class MessageDetector:
    def score(self, df):
        return self.model.predict_proba(self.features.transform(df)[ALL_COLS].values)[:, 1]

    def predict(self, df):
        return (self.score(df) >= self.threshold).astype(int)


_PICKLED_NAMES = {"MsgFeatures": MsgFeatures, "MessageDetector": MessageDetector}


def _load_model(path: Path):
    """joblib.load, with the notebook's `__main__` class names temporarily resolving to this module."""
    main = sys.modules["__main__"]
    missing = object()
    saved = {name: getattr(main, name, missing) for name in _PICKLED_NAMES}
    try:
        for name, cls in _PICKLED_NAMES.items():
            setattr(main, name, cls)
        return joblib.load(path)
    finally:
        for name, value in saved.items():
            if value is missing:
                delattr(main, name)
            else:
                setattr(main, name, value)


class AnomalyDetector:
    """Scores batches of SecurityEvent and flags those at or above the alert threshold."""

    def __init__(self, model_path: str | Path, threshold: float | None = None):
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"anomaly model not found: {path} (set ANOMALY_MODEL_PATH)")
        self._model = _load_model(path)  # trusted local artifact; joblib files are pickles
        self.threshold = float(threshold if threshold is not None else self._model.threshold)
        log.info("loaded anomaly model %s (threshold %.3f)", path.name, self.threshold)

    def score(self, events: list[SecurityEvent]) -> list[SecurityEvent]:
        if not events:
            return []
        frame = pd.DataFrame({"type": [e.severity for e in events], "line": [f"{e.severity} {e.message}" for e in events]})
        probs = self._model.score(frame)
        return [
            dataclasses.replace(e, anomaly_score=round(float(p), 4), is_anomaly=int(p >= self.threshold))
            for e, p in zip(events, probs)
        ]
