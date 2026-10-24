-- +goose NO TRANSACTION
-- +goose Up
CREATE TABLE IF NOT EXISTS security_logs_rejected (
    rejected_at DateTime64(3, 'UTC') DEFAULT now64(3),
    reason      String,
    raw         String
)
ENGINE = MergeTree
ORDER BY rejected_at;

-- +goose Down
DROP TABLE IF EXISTS security_logs_rejected;
