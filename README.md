# Stream-ETL

Logs Stream for analysis and anomaly detection.

Example:

> Log Analytics

```json
{
  "acceptcharset": "unknown",
  "acceptencoding": "deflate, gzip",
  "acceptlanguage": "unknown",
  "browsername": "Firefox",
  "browserversion": "107.0.0.0",
  "cachecontrol": "max-age=0",
  "city": "Decatur",
  "connection": "Keep-Alive",
  "contentlength": "unknown",
  "contenttype": "unknown",
  "country": "YT",
  "cpuarchitecture": "amd64",
  "devicemodel": "unknown",
  "devicetype": "unknown",
  "devicevendor": "unknown",
  "enginename": "Blink",
  "engineversion": "86.0.4240.80",
  "event_ts": "2026-10-06T16:56:28.175Z",
  "from": "unknown",
  "headers": "accept,accept-encoding,accept-language,connection,host,sec-ch-ua,sec-ch-ua-mobile,sec-ch-ua-platform,sec-fetch-dest,sec-fetch-mode,sec-fetch-site,sec-fetch-user,upgrade-insecure-requests,user-agent,x-forwarded-for,x-forwarded-host,x-forwarded-proto,x-real-ip,x-vercel-edge-region,x-vercel-id,x-vercel-ip-city,x-vercel-ip-country,x-vercel-ip-country-region,x-vercel-ip-latitude,x-vercel-ip-longitude,x-vercel-ip-timezone,x-vercel-proxied-for",
  "host": "https://log-analytics.tinybird.co",
  "ip_address": "0.199.1.195",
  "isbot": 0,
  "latitude": 76.8171,
  "log_level": "INFO",
  "log_message": "weber County FTM Electric Director Electric landscape Bacon Checking holistic",
  "longitude": -101.2579,
  "method": "PUT",
  "origin": "unknown",
  "osname": "Linux",
  "osversion": "4.2.2",
  "protocol": "https",
  "referer": "https://yandex.com/",
  "region": "BMU",
  "url": "https://log-analytics.tinybird.co/api/dummy/search",
  "useragent": "Opera/13.58 (X11; Linux x86_64; U; AR Presto/2.9.160 Version/11.00)",
  "via": "unknown",
  "xforwaredforip": "35.116.15.55"
}
```

## ETL pipeline

Mock-Data-Gen `security_logs` stream (NDJSON) -> extract -> transform -> detect -> load -> ClickHouse, with a Streamlit dashboard on top.

```
migrations/    goose SQL migrations for ClickHouse
src/stream_log_anamoly_detection/
  config/      environment settings
  extract/     HTTP stream client (auto-creates/starts the dataset, reconnects with backoff)
  transform/   validate, type-cast, enrich (severity_level, is_internal_source, is_off_hours)
  detection/   message RandomForest from ../anamoly_detection_ml (anomaly_score, is_anomaly)
  load/        batched ClickHouse inserts; invalid rows go to security_logs_rejected
  storage/     ClickHouse client, schema check, goose runner
  dashboard/   Streamlit app (pipeline flow, throughput, anomalies, data quality, migrations)
  pipeline.py  orchestration
  cli.py       `migrate`, `run` and `dashboard` commands
```

Tables (database `logs`): `security_logs` (ReplacingMergeTree, partitioned by month) and `security_logs_rejected`.
The schema is owned by [goose](https://github.com/pressly/goose); the app never creates tables itself.

```bash
cp .env.example .env
docker compose up -d                  # ClickHouse
# install the goose binary (go install github.com/pressly/goose/v3/cmd/goose@latest, or a release
# download) on PATH, in ./bin, or via GOOSE_BIN
python -m venv .venv && .venv/Scripts/activate   # Windows; use .venv/bin/activate elsewhere
pip install -e . pytest
python -m stream_log_anamoly_detection migrate           # goose up; also: migrate status | migrate down
# start Mock-Data-Gen on :8000 (see ../Mock-Data-Gen), then:
python -m stream_log_anamoly_detection run               # Ctrl+C to stop; --max-events N, --no-detection
python -m stream_log_anamoly_detection dashboard         # Streamlit on http://localhost:8501 (or: uv run app)
pytest
```

New schema changes: `goose -dir migrations create <name> sql`. ClickHouse has no transactional DDL, so every
migration starts with `-- +goose NO TRANSACTION` and must be idempotent (`IF NOT EXISTS`).

Detection uses `message_detector.joblib` (default `../anamoly_detection_ml/artifacts/`, override with
`ANOMALY_MODEL_PATH`). It is a pickle, so only load artifacts you trust, with scikit-learn 1.9.x. The alert threshold
comes from the model unless `ANOMALY_THRESHOLD` is set.
