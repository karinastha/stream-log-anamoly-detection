"""Orchestrates extract -> transform -> load for the security-log stream."""

import logging
from dataclasses import dataclass

import requests

from .config import Settings
from .detection import AnomalyDetector
from .extract import ensure_stream, stream_lines
from .load import ClickHouseLoader
from .storage import check_schema
from .transform import RejectedRecord, transform

log = logging.getLogger(__name__)


@dataclass(slots=True)
class RunStats:
    read: int = 0
    loaded: int = 0
    rejected: int = 0
    anomalies: int = 0


def run(settings: Settings, max_events: int | None = None) -> RunStats:
    """Stream events into ClickHouse until the source closes, `max_events` is reached, or Ctrl+C."""
    check_schema(settings)
    scorer = AnomalyDetector(settings.model_path, settings.anomaly_threshold).score if settings.detection_enabled else None
    if settings.auto_start_stream:
        ensure_stream(settings)

    loader = ClickHouseLoader(settings, scorer=scorer)
    stats = RunStats()
    try:
        for line in stream_lines(settings):
            stats.read += 1
            record = transform(line)
            if isinstance(record, RejectedRecord):
                log.debug("rejected: %s", record.reason)
            loader.add(record)
            if max_events is not None and stats.read >= max_events:
                break
    except KeyboardInterrupt:
        log.info("interrupted; flushing buffered records")
    finally:
        loader.close()
        stats.loaded, stats.rejected, stats.anomalies = loader.loaded, loader.rejected, loader.anomalies
    return stats


def check_source(settings: Settings) -> bool:
    try:
        requests.get(f"{settings.api_url}/datasets", timeout=5).raise_for_status()
        return True
    except requests.RequestException as exc:
        log.error("source API unreachable at %s: %s", settings.api_url, exc)
        return False
