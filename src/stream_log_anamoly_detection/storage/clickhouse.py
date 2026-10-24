"""ClickHouse connection helpers; the schema itself is managed by goose (see migrations/)."""

import re

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from ..config import Settings

EVENTS_TABLE = "security_logs"
REJECTED_TABLE = "security_logs_rejected"

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def get_client(settings: Settings, **kwargs) -> Client:
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database="default",
        **kwargs,
    )


def ensure_database(settings: Settings) -> None:
    """goose connects to the database named in its DSN, so it must exist before the first migration."""
    if not _IDENTIFIER.match(settings.clickhouse_db):
        raise ValueError(f"invalid database name: {settings.clickhouse_db!r}")
    client = get_client(settings)
    try:
        client.command(f"CREATE DATABASE IF NOT EXISTS {settings.clickhouse_db}")
    finally:
        client.close()


def check_schema(settings: Settings) -> None:
    """Raise if the migrated tables are missing (run `migrate up` first)."""
    client = get_client(settings)
    try:
        found = {
            row[0]: set(row[1])
            for row in client.query(
                "SELECT table, groupArray(name) FROM system.columns "
                "WHERE database = {db:String} AND table IN {tables:Array(String)} GROUP BY table",
                parameters={"db": settings.clickhouse_db, "tables": [EVENTS_TABLE, REJECTED_TABLE]},
            ).result_rows
        }
    finally:
        client.close()
    if EVENTS_TABLE not in found or REJECTED_TABLE not in found or "is_anomaly" not in found[EVENTS_TABLE]:
        raise RuntimeError(
            f"schema in database {settings.clickhouse_db!r} is missing or outdated; "
            "run `python -m stream_log_anamoly_detection migrate up`"
        )
