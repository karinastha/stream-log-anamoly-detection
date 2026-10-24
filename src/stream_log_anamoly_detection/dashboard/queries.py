"""ClickHouse queries behind the dashboard; each returns a pandas DataFrame."""

import re
from datetime import datetime, timedelta, timezone

import pandas as pd
from clickhouse_connect.driver.client import Client

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SINCE = "{since:DateTime64(3, 'UTC')}"

WINDOWS = {
    "Last 15 minutes": 15 * 60,
    "Last hour": 3600,
    "Last 6 hours": 6 * 3600,
    "Last 24 hours": 24 * 3600,
    "All time": None,
}


def window_start(seconds: int | None) -> datetime:
    if seconds is None:
        return datetime(1970, 1, 2, tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def bucket_seconds(seconds: int | None) -> int:
    """About 60 points per chart; 'All time' gets one-hour buckets."""
    return 3600 if seconds is None else max(10, seconds // 60)


class Queries:
    def __init__(self, client: Client, database: str):
        if not _IDENTIFIER.match(database):
            raise ValueError(f"invalid database name: {database!r}")
        self._client = client
        self._db = database

    def _df(self, sql: str, **parameters) -> pd.DataFrame:
        return self._client.query_df(sql, parameters=parameters)

    def totals(self, since: datetime) -> pd.Series:
        df = self._df(
            f"""
            SELECT count() AS events,
                   countIf(is_anomaly = 1) AS anomalies,
                   max(ingested_at) AS last_ingested,
                   uniqExact(source_ip) AS sources
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            """,
            since=since,
        )
        return df.iloc[0]

    def rejected_count(self, since: datetime) -> int:
        df = self._df(f"SELECT count() AS n FROM {self._db}.security_logs_rejected WHERE rejected_at >= {_SINCE}", since=since)
        return int(df.iloc[0, 0])

    def throughput(self, since: datetime, bucket: int) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT toStartOfInterval(ingested_at, toIntervalSecond({{bucket:UInt32}})) AS ts,
                   count() AS events,
                   countIf(is_anomaly = 1) AS anomalies
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            GROUP BY ts ORDER BY ts
            """,
            since=since, bucket=bucket,
        )

    def by_event_type(self, since: datetime) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT event_type, count() AS events, countIf(is_anomaly = 1) AS anomalies,
                   round(avg(anomaly_score), 4) AS avg_score
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            GROUP BY event_type ORDER BY anomalies DESC, events DESC
            """,
            since=since,
        )

    def anomalies_by_severity(self, since: datetime) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT severity, count() AS events, countIf(is_anomaly = 1) AS anomalies
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            GROUP BY severity ORDER BY max(severity_level)
            """,
            since=since,
        )

    def score_histogram(self, since: datetime) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT toFloat32(least(floor(anomaly_score * 20) / 20, 0.95)) AS score_bucket, count() AS events
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            GROUP BY score_bucket ORDER BY score_bucket
            """,
            since=since,
        )

    def top_alert_sources(self, since: datetime, limit: int = 10) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT toString(source_ip) AS source_ip, any(country) AS country, count() AS alerts,
                   uniqExact(event_type) AS event_types, round(max(anomaly_score), 3) AS max_score
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE} AND is_anomaly = 1
            GROUP BY source_ip ORDER BY alerts DESC LIMIT {{limit:UInt32}}
            """,
            since=since, limit=limit,
        )

    def recent_alerts(self, since: datetime, limit: int = 50) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT event_time, ingested_at, host, toString(source_ip) AS source_ip, username, event_type, severity,
                   anomaly_score, is_anomaly, message
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE} AND is_anomaly = 1
            ORDER BY ingested_at DESC, anomaly_score DESC LIMIT {{limit:UInt32}}
            """,
            since=since, limit=limit,
        )

    def latest_events(self, since: datetime, limit: int = 40) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT event_time, ingested_at, host, toString(source_ip) AS source_ip, username, event_type, severity,
                   anomaly_score, is_anomaly, message
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            ORDER BY ingested_at DESC, event_time DESC LIMIT {{limit:UInt32}}
            """,
            since=since, limit=limit,
        )

    def live_rate(self, seconds: int = 30) -> pd.Series:
        """Events and anomalies loaded during the last `seconds`."""
        since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        df = self._df(
            f"SELECT count() AS events, countIf(is_anomaly = 1) AS anomalies FROM {self._db}.security_logs WHERE ingested_at >= {_SINCE}",
            since=since,
        )
        return df.iloc[0]

    def recent_summary(self, seconds: int = 300) -> pd.Series:
        """Headline numbers for the last `seconds`, used by the live overview."""
        since = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        df = self._df(
            f"""
            SELECT count() AS events,
                   countIf(is_anomaly = 1) AS anomalies,
                   countIf(is_anomaly = 1 AND severity = 'CRITICAL') AS critical,
                   maxIf(severity_level, is_anomaly = 1) AS max_level,
                   uniqExact(source_ip) AS sources,
                   topK(1)(toString(source_ip))[1] AS top_source,
                   topK(1)(event_type)[1] AS top_type,
                   topKIf(1)(event_type, is_anomaly = 1)[1] AS top_flagged_type
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            """,
            since=since,
        )
        return df.iloc[0]

    def severity_timeline(self, since: datetime, bucket: int) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT toStartOfInterval(ingested_at, toIntervalSecond({{bucket:UInt32}})) AS ts, severity, count() AS events
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE}
            GROUP BY ts, severity ORDER BY ts
            """,
            since=since, bucket=bucket,
        )

    def incidents(self, since: datetime, limit: int = 30) -> pd.DataFrame:
        """Flagged events grouped by (source IP, event type); the most severe and strongest first."""
        return self._df(
            f"""
            SELECT toString(source_ip) AS source_ip, event_type, count() AS events,
                   min(event_time) AS first_seen, max(event_time) AS last_seen, max(ingested_at) AS last_ingested,
                   round(max(anomaly_score), 3) AS max_score,
                   argMax(severity, severity_level) AS severity, max(severity_level) AS peak_level,
                   any(country) AS country, any(username) AS username, any(host) AS host,
                   uniqExact(dest_ip) AS targets, uniqExact(dest_port) AS ports,
                   argMax(message, anomaly_score) AS sample
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE} AND is_anomaly = 1
            GROUP BY source_ip, event_type
            ORDER BY peak_level DESC, max_score DESC, last_ingested DESC LIMIT {{limit:UInt32}}
            """,
            since=since, limit=limit,
        )

    def incident_events(self, since: datetime, source_ip: str, event_type: str, limit: int = 30) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT event_time, ingested_at, host, toString(source_ip) AS source_ip, username, event_type, severity,
                   anomaly_score, is_anomaly, message
            FROM {self._db}.security_logs
            WHERE ingested_at >= {_SINCE} AND toString(source_ip) = {{ip:String}} AND event_type = {{etype:String}}
            ORDER BY event_time DESC LIMIT {{limit:UInt32}}
            """,
            since=since, ip=source_ip, etype=event_type, limit=limit,
        )

    def ip_history(self, source_ip: str) -> pd.Series:
        df = self._df(
            f"""
            SELECT count() AS events, countIf(is_anomaly = 1) AS anomalies, min(event_time) AS first_seen
            FROM {self._db}.security_logs
            WHERE source_ip = toIPv4({{ip:String}})
            """,
            ip=source_ip,
        )
        return df.iloc[0]

    def rejected_by_reason(self, since: datetime) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT reason, count() AS records
            FROM {self._db}.security_logs_rejected
            WHERE rejected_at >= {_SINCE}
            GROUP BY reason ORDER BY records DESC
            """,
            since=since,
        )

    def recent_rejected(self, since: datetime, limit: int = 20) -> pd.DataFrame:
        return self._df(
            f"""
            SELECT rejected_at, reason, raw
            FROM {self._db}.security_logs_rejected
            WHERE rejected_at >= {_SINCE}
            ORDER BY rejected_at DESC LIMIT {{limit:UInt32}}
            """,
            since=since, limit=limit,
        )
