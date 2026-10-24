"""Environment-based settings shared by every ETL stage."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_MODEL = _PROJECT_ROOT.parent / "anamoly_detection_ml" / "artifacts" / "message_detector.joblib"


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # ClickHouse: HTTP interface for the app, native protocol for goose
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_native_port: int = 9000
    clickhouse_user: str = "default"
    clickhouse_password: str = "clickhouse"
    clickhouse_db: str = "logs"

    # Migrations (goose)
    migrations_dir: str = str(_PROJECT_ROOT / "migrations")
    goose_bin: str = ""

    # Source: Mock-Data-Gen HTTP API
    api_url: str = "http://localhost:8000"
    dataset: str = "security_logs"
    auto_start_stream: bool = True
    events_per_second: int = 20
    anomalies_per_minute: float = 2.0
    stream_wait_seconds: int = 30
    max_retries: int = 5

    # Load
    batch_size: int = 1000
    flush_interval: float = 5.0

    # Detection
    detection_enabled: bool = True
    model_path: str = str(_DEFAULT_MODEL)
    anomaly_threshold: float | None = None  # None: use the threshold stored in the model

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        threshold = os.getenv("ANOMALY_THRESHOLD", "").strip()
        return cls(
            clickhouse_host=os.getenv("CLICKHOUSE_HOST", cls.clickhouse_host),
            clickhouse_port=int(os.getenv("CLICKHOUSE_PORT", cls.clickhouse_port)),
            clickhouse_native_port=int(os.getenv("CLICKHOUSE_NATIVE_PORT", cls.clickhouse_native_port)),
            clickhouse_user=os.getenv("CLICKHOUSE_USER", cls.clickhouse_user),
            clickhouse_password=os.getenv("CLICKHOUSE_PASSWORD", cls.clickhouse_password),
            clickhouse_db=os.getenv("CLICKHOUSE_DB", cls.clickhouse_db),
            migrations_dir=os.getenv("MIGRATIONS_DIR", cls.migrations_dir),
            goose_bin=os.getenv("GOOSE_BIN", cls.goose_bin),
            api_url=os.getenv("MOCK_API_URL", cls.api_url).rstrip("/"),
            dataset=os.getenv("MOCK_API_DATASET", cls.dataset),
            auto_start_stream=_bool("MOCK_API_AUTO_START", cls.auto_start_stream),
            events_per_second=int(os.getenv("MOCK_API_EPS", cls.events_per_second)),
            anomalies_per_minute=float(os.getenv("MOCK_API_ANOMALIES_PER_MINUTE", cls.anomalies_per_minute)),
            stream_wait_seconds=int(os.getenv("MOCK_API_STREAM_WAIT", cls.stream_wait_seconds)),
            max_retries=int(os.getenv("MOCK_API_MAX_RETRIES", cls.max_retries)),
            batch_size=int(os.getenv("ETL_BATCH_SIZE", cls.batch_size)),
            flush_interval=float(os.getenv("ETL_FLUSH_INTERVAL", cls.flush_interval)),
            detection_enabled=_bool("ANOMALY_DETECTION", cls.detection_enabled),
            model_path=os.getenv("ANOMALY_MODEL_PATH", cls.model_path),
            anomaly_threshold=float(threshold) if threshold else None,
        )
