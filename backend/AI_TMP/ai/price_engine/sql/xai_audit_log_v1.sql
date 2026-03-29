CREATE TABLE IF NOT EXISTS xai_audit_log_v1 (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    item_id TEXT NOT NULL,
    raw_source_refs JSONB NOT NULL,
    normalization_steps JSONB NOT NULL,
    feature_snapshot_id TEXT NOT NULL,
    model_input_vector_hash TEXT NOT NULL,
    fired_rule_ids JSONB NOT NULL,
    feature_contributions JSONB NOT NULL,
    final_decision TEXT NOT NULL,
    rendered_explanation TEXT NOT NULL,
    model_version TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    data_snapshot_id TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xai_audit_log_snapshot
ON xai_audit_log_v1 (data_snapshot_id);

CREATE INDEX IF NOT EXISTS idx_xai_audit_log_model_rule
ON xai_audit_log_v1 (model_version, rule_version);
