-- +goose NO TRANSACTION
-- +goose Up
CREATE TABLE IF NOT EXISTS security_logs (
    event_id           UUID,
    event_time         DateTime64(3, 'UTC'),
    ingested_at        DateTime64(3, 'UTC') DEFAULT now64(3),
    host               LowCardinality(String),
    source_ip          IPv4,
    dest_ip            IPv4,
    dest_port          UInt16,
    username           LowCardinality(String),
    event_type         LowCardinality(String),
    severity           LowCardinality(String),
    severity_level     UInt8,
    country            LowCardinality(String),
    bytes_out          UInt64,
    message            String,
    is_internal_source UInt8,
    is_off_hours       UInt8
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_type, host, event_time, event_id);

-- +goose Down
DROP TABLE IF EXISTS security_logs;
