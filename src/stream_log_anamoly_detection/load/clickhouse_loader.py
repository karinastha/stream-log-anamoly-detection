"""Load: buffer transformed records and batch-insert them into ClickHouse."""

import logging
import time
from collections.abc import Callable

from ..config import Settings
from ..storage import EVENTS_TABLE, REJECTED_TABLE, get_client
from ..transform import EVENT_COLUMNS, RejectedRecord, SecurityEvent

log = logging.getLogger(__name__)

_INSERT_ATTEMPTS = 3

Scorer = Callable[[list[SecurityEvent]], list[SecurityEvent]]


class ClickHouseLoader:
    def __init__(self, settings: Settings, client=None, scorer: Scorer | None = None):
        self._settings = settings
        self._client = client or get_client(settings)
        self._scorer = scorer
        self._events: list[SecurityEvent] = []
        self._rejected: list[list] = []
        self._last_flush = time.monotonic()
        self.loaded = 0
        self.rejected = 0
        self.anomalies = 0

    def add(self, record: SecurityEvent | RejectedRecord) -> None:
        if isinstance(record, RejectedRecord):
            self._rejected.append([record.reason, record.raw])
        else:
            self._events.append(record)
        if self._due():
            self.flush()

    def _due(self) -> bool:
        pending = len(self._events) + len(self._rejected)
        return pending >= self._settings.batch_size or (
            pending > 0 and time.monotonic() - self._last_flush >= self._settings.flush_interval
        )

    def flush(self) -> None:
        if self._events:
            events = self._scorer(self._events) if self._scorer else self._events
            self._insert(EVENTS_TABLE, [e.as_row() for e in events], list(EVENT_COLUMNS))
            flagged = sum(e.is_anomaly for e in events)
            self.loaded += len(events)
            self.anomalies += flagged
            log.info("loaded %d events, %d anomalies (total %d / %d)", len(events), flagged, self.loaded, self.anomalies)
            self._events = []
        if self._rejected:
            self._insert(REJECTED_TABLE, self._rejected, ["reason", "raw"])
            self.rejected += len(self._rejected)
            log.warning("stored %d rejected records (total %d)", len(self._rejected), self.rejected)
            self._rejected = []
        self._last_flush = time.monotonic()

    def _insert(self, table: str, rows: list[list], columns: list[str]) -> None:
        for attempt in range(1, _INSERT_ATTEMPTS + 1):
            try:
                self._client.insert(table, rows, column_names=columns, database=self._settings.clickhouse_db)
                return
            except Exception as exc:
                if attempt == _INSERT_ATTEMPTS:
                    raise
                log.warning("insert into %s failed (%s); retry %d/%d", table, exc, attempt, _INSERT_ATTEMPTS - 1)
                time.sleep(2 ** attempt)

    def close(self) -> None:
        try:
            self.flush()
        finally:
            self._client.close()
