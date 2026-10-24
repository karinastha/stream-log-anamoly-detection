-- +goose NO TRANSACTION
-- +goose Up
ALTER TABLE security_logs
    ADD COLUMN IF NOT EXISTS anomaly_score Float32 DEFAULT 0,
    ADD COLUMN IF NOT EXISTS is_anomaly    UInt8   DEFAULT 0;

-- +goose Down
ALTER TABLE security_logs
    DROP COLUMN IF EXISTS anomaly_score,
    DROP COLUMN IF EXISTS is_anomaly;
