import json
from datetime import timezone

from stream_log_anamoly_detection.transform import RejectedRecord, SecurityEvent, transform

VALID = {
    "event_id": "6f1c1c64-7a0e-4c9e-9d0c-5a1b7a1c2d3e",
    "timestamp": "2026-10-21 02:15:30.123",
    "host": "auth-01",
    "source_ip": "185.10.20.30",
    "dest_ip": "10.0.30.5",
    "dest_port": 22,
    "username": "root",
    "event_type": "login_failed",
    "severity": "warning",
    "country": "DE",
    "bytes_out": 0,
    "message": "Failed password",
}


def test_valid_event_is_typed_and_enriched():
    event = transform(json.dumps(VALID))
    assert isinstance(event, SecurityEvent)
    assert event.event_time.tzinfo is timezone.utc
    assert event.event_time.microsecond == 123000
    assert event.severity == "WARNING" and event.severity_level == 2
    assert event.is_internal_source == 0
    assert event.is_off_hours == 1


def test_internal_source_and_business_hours():
    row = {**VALID, "source_ip": "10.0.1.10", "timestamp": "2026-10-21 12:00:00.000"}
    event = transform(json.dumps(row))
    assert event.is_internal_source == 1 and event.is_off_hours == 0


def test_as_row_matches_columns():
    from stream_log_anamoly_detection.transform import EVENT_COLUMNS

    assert len(transform(json.dumps(VALID)).as_row()) == len(EVENT_COLUMNS)


def test_rejects_bad_input():
    cases = {
        "not json": "invalid json",
        "[1]": "json value is not an object",
        json.dumps({**VALID, "event_id": "x"}): "invalid event_id",
        json.dumps({**VALID, "timestamp": "yesterday"}): "invalid timestamp",
        json.dumps({**VALID, "source_ip": "999.1.1.1"}): "invalid ip address",
        json.dumps({**VALID, "dest_port": 70000}): "dest_port out of range",
        json.dumps({**VALID, "bytes_out": "lots"}): "non-numeric dest_port or bytes_out",
        json.dumps({**VALID, "event_type": ""}): "missing event_type",
    }
    for raw, reason in cases.items():
        result = transform(raw)
        assert isinstance(result, RejectedRecord) and result.reason == reason, raw
