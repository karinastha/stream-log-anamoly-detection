"""Transform: validate, type-cast and enrich raw security-log lines."""

import ipaddress
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

SEVERITY_LEVELS = {"INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}

# Column order of the `security_logs` table (ingested_at is filled by ClickHouse).
EVENT_COLUMNS = (
    "event_id", "event_time", "host", "source_ip", "dest_ip", "dest_port", "username", "event_type",
    "severity", "severity_level", "country", "bytes_out", "message", "is_internal_source", "is_off_hours",
    "anomaly_score", "is_anomaly",
)


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    event_id: uuid.UUID
    event_time: datetime
    host: str
    source_ip: ipaddress.IPv4Address
    dest_ip: ipaddress.IPv4Address
    dest_port: int
    username: str
    event_type: str
    severity: str
    severity_level: int
    country: str
    bytes_out: int
    message: str
    is_internal_source: int
    is_off_hours: int
    anomaly_score: float = 0.0  # set by the detection stage
    is_anomaly: int = 0

    def as_row(self) -> list:
        return [getattr(self, column) for column in EVENT_COLUMNS]


@dataclass(frozen=True, slots=True)
class RejectedRecord:
    raw: str
    reason: str


def _parse_time(value: str) -> datetime:
    ts = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts.astimezone(timezone.utc)


def _text(row: dict, key: str, default: str = "") -> str:
    value = row.get(key)
    return default if value is None else str(value).strip()


def transform(raw: str) -> SecurityEvent | RejectedRecord:
    """Parse one NDJSON line; anything invalid becomes a RejectedRecord instead of raising."""
    try:
        row = json.loads(raw)
    except ValueError:
        return RejectedRecord(raw, "invalid json")
    if not isinstance(row, dict):
        return RejectedRecord(raw, "json value is not an object")

    try:
        event_id = uuid.UUID(_text(row, "event_id"))
    except ValueError:
        return RejectedRecord(raw, "invalid event_id")
    try:
        event_time = _parse_time(_text(row, "timestamp"))
    except ValueError:
        return RejectedRecord(raw, "invalid timestamp")
    try:
        source_ip = ipaddress.IPv4Address(_text(row, "source_ip"))
        dest_ip = ipaddress.IPv4Address(_text(row, "dest_ip"))
    except ValueError:
        return RejectedRecord(raw, "invalid ip address")
    try:
        dest_port = int(row.get("dest_port") or 0)
        bytes_out = int(row.get("bytes_out") or 0)
    except (TypeError, ValueError):
        return RejectedRecord(raw, "non-numeric dest_port or bytes_out")
    if not 0 <= dest_port <= 65535:
        return RejectedRecord(raw, "dest_port out of range")
    if bytes_out < 0:
        return RejectedRecord(raw, "negative bytes_out")

    event_type = _text(row, "event_type")
    if not event_type:
        return RejectedRecord(raw, "missing event_type")

    severity = _text(row, "severity", "INFO").upper()
    return SecurityEvent(
        event_id=event_id,
        event_time=event_time,
        host=_text(row, "host", "unknown"),
        source_ip=source_ip,
        dest_ip=dest_ip,
        dest_port=dest_port,
        username=_text(row, "username", "-"),
        event_type=event_type,
        severity=severity,
        severity_level=SEVERITY_LEVELS.get(severity, 0),
        country=_text(row, "country", "unknown"),
        bytes_out=bytes_out,
        message=_text(row, "message"),
        is_internal_source=int(source_ip.is_private),
        is_off_hours=int(event_time.hour < 6 or event_time.hour >= 22),
    )
