"""Run goose (https://github.com/pressly/goose) migrations against ClickHouse."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from ..config import Settings
from .clickhouse import ensure_database

_BIN_DIR = Path(__file__).resolve().parents[3] / "bin"


def find_goose(settings: Settings) -> str:
    candidates = [settings.goose_bin, shutil.which("goose"), str(_BIN_DIR / "goose.exe"), str(_BIN_DIR / "goose")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        "goose binary not found. Install it (https://github.com/pressly/goose/releases), "
        "put it on PATH, or set GOOSE_BIN."
    )


def dsn(settings: Settings) -> str:
    # goose's clickhouse driver speaks the native protocol
    return (
        f"clickhouse://{quote(settings.clickhouse_user, safe='')}:{quote(settings.clickhouse_password, safe='')}"
        f"@{settings.clickhouse_host}:{settings.clickhouse_native_port}/{settings.clickhouse_db}"
    )


def run_goose(settings: Settings, command: str = "up", *args: str) -> int:
    """Run a goose command (up, down, status, version, ...) and return its exit code."""
    binary = find_goose(settings)
    if command == "up":
        ensure_database(settings)
    env = {
        **os.environ,
        "GOOSE_DRIVER": "clickhouse",
        "GOOSE_DBSTRING": dsn(settings),  # via env so the password stays out of the process list
        "GOOSE_MIGRATION_DIR": settings.migrations_dir,
    }
    result = subprocess.run([binary, command, *args], env=env, stdout=sys.stdout, stderr=sys.stderr, check=False)
    return result.returncode
