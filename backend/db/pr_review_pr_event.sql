CREATE TABLE IF NOT EXISTS pr_reviews (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    decision VARCHAR(30) NOT NULL,
    content TEXT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT uk_pr_reviews_post_user UNIQUE (post_id, user_id)
);

CREATE TABLE IF NOT EXISTS pr_events (
    id BIGSERIAL PRIMARY KEY,
    post_id BIGINT NOT NULL,
    actor_user_id BIGINT NULL,
    event_type VARCHAR(40) NOT NULL,
    payload TEXT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pr_reviews_post_id ON pr_reviews(post_id);
CREATE INDEX IF NOT EXISTS idx_pr_events_post_id ON pr_events(post_id);
