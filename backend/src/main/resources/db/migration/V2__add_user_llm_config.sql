CREATE TABLE IF NOT EXISTS user_llm_config (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT       NOT NULL,
    use_custom  TINYINT      NOT NULL DEFAULT 0 COMMENT '0=server default, 1=custom',
    base_url    VARCHAR(512)          DEFAULT NULL,
    api_key     VARCHAR(256)          DEFAULT NULL,
    model       VARCHAR(128)          DEFAULT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
