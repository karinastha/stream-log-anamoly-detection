import json
from dataclasses import replace

from stream_log_anamoly_detection.config import Settings
from stream_log_anamoly_detection.load import ClickHouseLoader
from stream_log_anamoly_detection.transform import transform

from .test_transform import VALID


class FakeClient:
    def __init__(self):
        self.inserts = []
        self.closed = False

    def insert(self, table, rows, column_names, database):
        self.inserts.append((table, len(rows), database))

    def close(self):
        self.closed = True


def test_flushes_when_batch_is_full_and_on_close():
    client = FakeClient()
    loader = ClickHouseLoader(Settings(batch_size=2, flush_interval=3600), client=client)
    for _ in range(3):
        loader.add(transform(json.dumps(VALID)))
    assert client.inserts == [("security_logs", 2, "logs")]

    loader.add(transform("garbage"))  # pending (1 event + 1 rejected) reaches batch_size
    assert client.inserts[1:] == [("security_logs", 1, "logs"), ("security_logs_rejected", 1, "logs")]

    loader.add(transform(json.dumps(VALID)))
    loader.close()
    assert client.inserts[3:] == [("security_logs", 1, "logs")]
    assert client.closed and loader.loaded == 4 and loader.rejected == 1


def test_scorer_runs_before_insert():
    client = FakeClient()
    flagged = []

    def scorer(events):
        flagged.extend(events)
        return [replace(e, anomaly_score=0.9, is_anomaly=1) for e in events]

    loader = ClickHouseLoader(Settings(batch_size=10), client=client, scorer=scorer)
    loader.add(transform(json.dumps(VALID)))
    loader.close()
    assert len(flagged) == 1 and loader.anomalies == 1
