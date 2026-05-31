-- ============================================================================
-- Email System — V2 增量迁移（基于 V1__init_schema.sql）
--
-- 本脚本仅包含相对 V1 的增量变更：
--   1. 新增列（无 DROP / 无列重命名 / 无表重建）
--   2. 补充索引
--   3. 补充外键约束与 CHECK 约束
--   4. 统一 DATETIME → DATETIME(3)（毫秒精度）
--   5. 补充智能分析相关表的软删除与审计字段
--   6. 种子数据（默认角色）
--
-- 安全声明：本脚本不会删除任何已有表或数据。
-- ============================================================================

-- ============================================================================
-- 1. sys_user — 补充列 + 索引 + 时间精度
-- ============================================================================
ALTER TABLE sys_user
    ADD COLUMN avatar_url    VARCHAR(512)  COMMENT '头像URL',
    ADD COLUMN last_login_at DATETIME(3)   COMMENT '最后登录时间',
    ADD COLUMN last_login_ip VARCHAR(64)   COMMENT '最后登录IP';

ALTER TABLE sys_user
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
    MODIFY COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                    COMMENT '更新时间';

CREATE INDEX idx_user_status ON sys_user (status);
CREATE INDEX idx_user_email  ON sys_user (email);

-- ============================================================================
-- 2. sys_role — 补充列 + 时间精度
-- ============================================================================
ALTER TABLE sys_role
    ADD COLUMN description VARCHAR(255)  COMMENT '角色描述',
    ADD COLUMN updated_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                     COMMENT '更新时间',
    ADD COLUMN deleted     TINYINT(1)  NOT NULL DEFAULT 0                     COMMENT '软删除标记';

ALTER TABLE sys_role
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间';

-- ============================================================================
-- 3. sys_user_role — 补充审计列 + 外键 + 索引
-- ============================================================================
ALTER TABLE sys_user_role
    ADD COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                     COMMENT '创建时间',
    ADD COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                                        COMMENT '更新时间',
    ADD COLUMN deleted    TINYINT(1)  NOT NULL DEFAULT 0                                        COMMENT '软删除标记';

ALTER TABLE sys_user_role
    ADD CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE;

CREATE INDEX idx_user_role_user ON sys_user_role (user_id);
CREATE INDEX idx_user_role_role ON sys_user_role (role_id);

-- ============================================================================
-- 4. mail_account — 补充外键 + 索引 + 时间精度
-- ============================================================================
ALTER TABLE mail_account
    MODIFY COLUMN last_sync_at DATETIME(3)                                            COMMENT '最后同步时间',
    MODIFY COLUMN created_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间',
    MODIFY COLUMN updated_at   DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                               ON UPDATE CURRENT_TIMESTAMP(3)                         COMMENT '更新时间';

ALTER TABLE mail_account
    ADD CONSTRAINT fk_account_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE;

CREATE INDEX idx_account_email  ON mail_account (email_address);
CREATE INDEX idx_account_status ON mail_account (status);

-- ============================================================================
-- 5. mail_folder — 补充列 + 外键 + CHECK + 索引 + 时间精度
-- ============================================================================
ALTER TABLE mail_folder
    ADD COLUMN sort_order INT        NOT NULL DEFAULT 0  COMMENT '排序序号',
    ADD COLUMN deleted    TINYINT(1) NOT NULL DEFAULT 0  COMMENT '软删除标记';

ALTER TABLE mail_folder
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间',
    MODIFY COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                               ON UPDATE CURRENT_TIMESTAMP(3)                         COMMENT '更新时间';

ALTER TABLE mail_folder
    ADD CONSTRAINT fk_folder_user    FOREIGN KEY (user_id)    REFERENCES sys_user (id)     ON DELETE CASCADE,
    ADD CONSTRAINT fk_folder_account FOREIGN KEY (account_id) REFERENCES mail_account (id) ON DELETE CASCADE;

-- MySQL 8.0.16+ 支持 CHECK 约束；若版本较低请注释以下语句
ALTER TABLE mail_folder
    ADD CONSTRAINT chk_folder_type CHECK (type IN ('inbox', 'sent', 'draft', 'trash', 'spam', 'custom'));

CREATE INDEX idx_folder_account ON mail_folder (account_id);
CREATE INDEX idx_folder_type    ON mail_folder (type);

-- ============================================================================
-- 6. mail_message — 补充列 + 外键 + 索引 + 时间精度
-- （保留 V1 的 message_id 字段名，不做重命名）
-- ============================================================================
ALTER TABLE mail_message
    ADD COLUMN size_bytes BIGINT NOT NULL DEFAULT 0 COMMENT '邮件大小（字节）';

ALTER TABLE mail_message
    MODIFY COLUMN sent_at     DATETIME(3)                                            COMMENT '发件时间',
    MODIFY COLUMN received_at DATETIME(3)                                            COMMENT '收件时间',
    MODIFY COLUMN created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间',
    MODIFY COLUMN updated_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                              ON UPDATE CURRENT_TIMESTAMP(3)                         COMMENT '更新时间';

ALTER TABLE mail_message
    ADD CONSTRAINT fk_message_user    FOREIGN KEY (user_id)    REFERENCES sys_user (id)     ON DELETE CASCADE,
    ADD CONSTRAINT fk_message_account FOREIGN KEY (account_id) REFERENCES mail_account (id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_message_folder  FOREIGN KEY (folder_id)  REFERENCES mail_folder (id)  ON DELETE SET NULL;

CREATE INDEX idx_message_read_flag    ON mail_message (read_flag);
CREATE INDEX idx_message_deleted_flag ON mail_message (deleted_flag);
CREATE INDEX idx_message_received_at  ON mail_message (received_at);
CREATE INDEX idx_message_sent_at      ON mail_message (sent_at);
CREATE INDEX idx_message_from_address ON mail_message (from_address);

-- ============================================================================
-- 7. mail_recipient — 补充审计列 + 外键 + CHECK + 索引
-- ============================================================================
ALTER TABLE mail_recipient
    ADD COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                     COMMENT '创建时间',
    ADD COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                                        COMMENT '更新时间',
    ADD COLUMN deleted    TINYINT(1)  NOT NULL DEFAULT 0                                        COMMENT '软删除标记';

ALTER TABLE mail_recipient
    ADD CONSTRAINT fk_recipient_message FOREIGN KEY (message_id) REFERENCES mail_message (id) ON DELETE CASCADE;

ALTER TABLE mail_recipient
    ADD CONSTRAINT chk_recipient_type CHECK (type IN ('to', 'cc', 'bcc'));

CREATE INDEX idx_recipient_type ON mail_recipient (type);

-- ============================================================================
-- 8. mail_attachment — 补充列 + 外键 + CHECK
-- ============================================================================
ALTER TABLE mail_attachment
    ADD COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                                        COMMENT '更新时间';

ALTER TABLE mail_attachment
    ADD CONSTRAINT fk_attachment_user    FOREIGN KEY (user_id)    REFERENCES sys_user (id)      ON DELETE CASCADE,
    ADD CONSTRAINT fk_attachment_message FOREIGN KEY (message_id) REFERENCES mail_message (id) ON DELETE SET NULL;

ALTER TABLE mail_attachment
    ADD CONSTRAINT chk_attachment_storage CHECK (storage_type IN ('local', 'minio'));

-- ============================================================================
-- 9. contact — 补充列 + 外键 + 索引
-- ============================================================================
ALTER TABLE contact
    ADD COLUMN company    VARCHAR(128) COMMENT '公司名称',
    ADD COLUMN department VARCHAR(128) COMMENT '部门名称';

ALTER TABLE contact
    ADD CONSTRAINT fk_contact_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE;

CREATE INDEX idx_contact_user  ON contact (user_id);
CREATE INDEX idx_contact_name  ON contact (name);
CREATE INDEX idx_contact_email ON contact (email_address);

-- ============================================================================
-- 10. login_audit — 补充列 + 外键 + 索引
-- ============================================================================
ALTER TABLE login_audit
    ADD COLUMN deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '软删除标记（GDPR数据清除）';

ALTER TABLE login_audit
    ADD CONSTRAINT fk_login_audit_user FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE SET NULL;

CREATE INDEX idx_login_audit_created_at ON login_audit (created_at);
CREATE INDEX idx_login_audit_success    ON login_audit (success);
CREATE INDEX idx_login_audit_ip         ON login_audit (ip_address);
CREATE INDEX idx_login_audit_user_time  ON login_audit (user_id, created_at);

-- ============================================================================
-- 11. 智能分析相关表 — 补充软删除与审计字段（V1 已有基础表结构）
-- ============================================================================

-- 11.1 mail_intelligence_result — 补充软删除 + 时间精度
ALTER TABLE mail_intelligence_result
    ADD COLUMN deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '软删除标记';

ALTER TABLE mail_intelligence_result
    MODIFY COLUMN analyzed_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '分析完成时间',
    MODIFY COLUMN created_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间',
    MODIFY COLUMN updated_at  DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                              ON UPDATE CURRENT_TIMESTAMP(3)                         COMMENT '更新时间';

-- 11.2 mail_threat_indicator — 补充审计列 + 时间精度
ALTER TABLE mail_threat_indicator
    ADD COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                                        COMMENT '更新时间',
    ADD COLUMN deleted    TINYINT(1)  NOT NULL DEFAULT 0                                        COMMENT '软删除标记';

ALTER TABLE mail_threat_indicator
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间';

-- 11.3 mail_push_event — 补充审计列 + 时间精度
ALTER TABLE mail_push_event
    ADD COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                           ON UPDATE CURRENT_TIMESTAMP(3)                                        COMMENT '更新时间',
    ADD COLUMN deleted    TINYINT(1)  NOT NULL DEFAULT 0                                        COMMENT '软删除标记';

ALTER TABLE mail_push_event
    MODIFY COLUMN pushed_at  DATETIME(3)                                            COMMENT '推送时间',
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间';

-- 11.4 intelligence_plugin — 补充软删除
ALTER TABLE intelligence_plugin
    ADD COLUMN deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '软删除标记';

ALTER TABLE intelligence_plugin
    MODIFY COLUMN created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)      COMMENT '创建时间',
    MODIFY COLUMN updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                              ON UPDATE CURRENT_TIMESTAMP(3)                         COMMENT '更新时间';

-- ============================================================================
-- 种子数据 — 默认角色
-- ============================================================================
INSERT INTO sys_role (code, name, description) VALUES
    ('admin', '管理员', '系统管理员，拥有全部权限'),
    ('user',  '普通用户', '普通用户，拥有基本功能权限')
ON DUPLICATE KEY UPDATE name = VALUES(name);
