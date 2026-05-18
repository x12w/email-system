-- ============================================================================
-- Email System Database Initialization Script
-- MySQL 8.0+ | Charset: utf8mb4 | Collation: utf8mb4_0900_ai_ci
--
-- This script is idempotent: DROP IF EXISTS + CREATE ensures safe re-runs.
-- Tables are ordered by FK dependency so creation always succeeds.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS email_system
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci;

USE email_system;

-- ============================================================================
-- Drop all tables in reverse dependency order (children before parents)
-- ============================================================================
DROP TABLE IF EXISTS mail_recipient;
DROP TABLE IF EXISTS mail_attachment;
DROP TABLE IF EXISTS mail_message;
DROP TABLE IF EXISTS mail_folder;
DROP TABLE IF EXISTS mail_account;
DROP TABLE IF EXISTS sys_user_role;
DROP TABLE IF EXISTS login_audit;
DROP TABLE IF EXISTS contact;
DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_role;

-- ============================================================================
-- 1. sys_role — 角色表 (no FK inbound; reference target for sys_user_role)
-- ============================================================================
CREATE TABLE sys_role (
    id          BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    code        VARCHAR(64)     NOT NULL                                              COMMENT '角色编码（admin / user）',
    name        VARCHAR(64)     NOT NULL                                              COMMENT '角色显示名称',
    description VARCHAR(255)                                                         COMMENT '角色描述',
    created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted     TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_role_code    UNIQUE KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='角色表';

-- ============================================================================
-- 2. sys_user — 系统用户表
-- ============================================================================
CREATE TABLE sys_user (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    username        VARCHAR(64)     NOT NULL                                              COMMENT '用户名',
    password_hash   VARCHAR(255)    NOT NULL                                              COMMENT '密码哈希（BCrypt）',
    display_name    VARCHAR(64)     NOT NULL                                              COMMENT '显示名称',
    email           VARCHAR(255)                                                         COMMENT '恢复/通知邮箱',
    avatar_url      VARCHAR(512)                                                         COMMENT '头像URL',
    status          TINYINT(1)      NOT NULL DEFAULT 1                                    COMMENT '状态：1=启用 0=禁用',
    last_login_at   DATETIME(3)                                                          COMMENT '最后登录时间',
    last_login_ip   VARCHAR(64)                                                          COMMENT '最后登录IP',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_user_username UNIQUE KEY (username),
    INDEX       idx_user_status  (status),
    INDEX       idx_user_email   (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户表';

-- ============================================================================
-- 3. sys_user_role — 用户-角色关联表
-- ============================================================================
CREATE TABLE sys_user_role (
    id          BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id     BIGINT          NOT NULL                                              COMMENT '用户ID（关联sys_user）',
    role_id     BIGINT          NOT NULL                                              COMMENT '角色ID（关联sys_role）',
    created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted     TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_user_role_pair    UNIQUE KEY (user_id, role_id),
    CONSTRAINT fk_user_role_user    FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role    FOREIGN KEY (role_id) REFERENCES sys_role (id) ON DELETE CASCADE,
    INDEX       idx_user_role_user  (user_id),
    INDEX       idx_user_role_role  (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户角色关联表';

-- ============================================================================
-- 4. mail_account — 邮箱账号表
-- ============================================================================
CREATE TABLE mail_account (
    id                      BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id                 BIGINT          NOT NULL                                              COMMENT '所属用户ID',
    email_address           VARCHAR(255)    NOT NULL                                              COMMENT '邮箱地址',
    display_name            VARCHAR(128)                                                          COMMENT '发件显示名称',
    smtp_host               VARCHAR(255)    NOT NULL                                              COMMENT 'SMTP服务器地址',
    smtp_port               INT             NOT NULL                                              COMMENT 'SMTP端口',
    smtp_ssl                TINYINT(1)      NOT NULL DEFAULT 1                                    COMMENT 'SMTP SSL：1=启用 0=关闭',
    imap_host               VARCHAR(255)                                                          COMMENT 'IMAP服务器地址',
    imap_port               INT                                                                   COMMENT 'IMAP端口',
    imap_ssl                TINYINT(1)      NOT NULL DEFAULT 1                                    COMMENT 'IMAP SSL：1=启用 0=关闭',
    auth_username           VARCHAR(255)    NOT NULL                                              COMMENT '认证用户名',
    auth_password_encrypted VARCHAR(512)    NOT NULL                                              COMMENT '加密后的认证密码',
    status                  TINYINT(1)      NOT NULL DEFAULT 1                                    COMMENT '状态：1=启用 0=禁用',
    last_sync_at            DATETIME(3)                                                           COMMENT '最后同步时间',
    created_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                            ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted                 TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT fk_account_user   FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
    INDEX       idx_account_user      (user_id),
    INDEX       idx_account_email     (email_address),
    INDEX       idx_account_status    (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='邮箱账号表';

-- ============================================================================
-- 5. mail_folder — 邮件文件夹表
-- ============================================================================
CREATE TABLE mail_folder (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id         BIGINT          NOT NULL                                              COMMENT '所属用户ID',
    account_id      BIGINT          NOT NULL                                              COMMENT '所属账号ID',
    name            VARCHAR(128)    NOT NULL                                              COMMENT '文件夹显示名称',
    remote_name     VARCHAR(255)                                                         COMMENT '远程文件夹原始名称',
    type            VARCHAR(32)     NOT NULL                                              COMMENT '文件夹类型：inbox/sent/draft/trash/spam/custom',
    unread_count    INT             NOT NULL DEFAULT 0                                    COMMENT '未读邮件数',
    total_count     INT             NOT NULL DEFAULT 0                                    COMMENT '邮件总数',
    sort_order      INT             NOT NULL DEFAULT 0                                    COMMENT '排序序号',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_folder_account_remote  UNIQUE KEY (account_id, remote_name),
    CONSTRAINT fk_folder_user            FOREIGN KEY (user_id)    REFERENCES sys_user (id)     ON DELETE CASCADE,
    CONSTRAINT fk_folder_account         FOREIGN KEY (account_id) REFERENCES mail_account (id) ON DELETE CASCADE,
    CONSTRAINT chk_folder_type           CHECK (type IN ('inbox', 'sent', 'draft', 'trash', 'spam', 'custom')),
    INDEX       idx_folder_user      (user_id),
    INDEX       idx_folder_account   (account_id),
    INDEX       idx_folder_type      (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='邮件文件夹表';

-- ============================================================================
-- 6. mail_message — 邮件主表
-- ============================================================================
CREATE TABLE mail_message (
    id                  BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id             BIGINT          NOT NULL                                              COMMENT '所属用户ID',
    account_id          BIGINT          NOT NULL                                              COMMENT '所属账号ID',
    folder_id           BIGINT                                                                COMMENT '当前所在文件夹ID',
    message_uid         VARCHAR(255)                                                          COMMENT 'IMAP消息UID',
    message_id_header   VARCHAR(512)                                                          COMMENT 'RFC 5322 Message-ID 头',
    from_address        VARCHAR(255)    NOT NULL                                              COMMENT '发件人邮箱地址',
    from_name           VARCHAR(255)                                                          COMMENT '发件人显示名称',
    subject             VARCHAR(512)                                                          COMMENT '邮件主题',
    content_type        VARCHAR(32)     NOT NULL DEFAULT 'html'                               COMMENT '内容类型：text/html',
    content             MEDIUMTEXT                                                            COMMENT '邮件正文（HTML/纯文本）',
    preview             VARCHAR(512)                                                          COMMENT '正文预览摘要',
    sent_at             DATETIME(3)                                                           COMMENT '发件时间',
    received_at         DATETIME(3)                                                           COMMENT '收件时间',
    size_bytes          BIGINT          NOT NULL DEFAULT 0                                    COMMENT '邮件大小（字节）',
    read_flag           TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '已读标记：0=未读 1=已读',
    star_flag           TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '星标标记：0=否 1=是',
    draft_flag          TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '草稿标记：0=否 1=是',
    deleted_flag        TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '删除标记：0=否 1=是（回收站）',
    attachment_count    INT             NOT NULL DEFAULT 0                                    COMMENT '附件数量',
    created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                        ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted             TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_message_account_uid   UNIQUE KEY (account_id, message_uid),
    CONSTRAINT fk_message_user          FOREIGN KEY (user_id)    REFERENCES sys_user (id)     ON DELETE CASCADE,
    CONSTRAINT fk_message_account       FOREIGN KEY (account_id) REFERENCES mail_account (id) ON DELETE CASCADE,
    CONSTRAINT fk_message_folder        FOREIGN KEY (folder_id)  REFERENCES mail_folder (id)  ON DELETE SET NULL,
    INDEX       idx_message_user_folder_time  (user_id, folder_id, received_at),
    INDEX       idx_message_subject           (subject),
    INDEX       idx_message_read_flag         (read_flag),
    INDEX       idx_message_deleted_flag      (deleted_flag),
    INDEX       idx_message_received_at       (received_at),
    INDEX       idx_message_sent_at           (sent_at),
    INDEX       idx_message_from_address      (from_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='邮件主表';

-- ============================================================================
-- 7. mail_recipient — 邮件收件人表
-- ============================================================================
CREATE TABLE mail_recipient (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    message_id      BIGINT          NOT NULL                                              COMMENT '所属邮件ID',
    type            VARCHAR(16)     NOT NULL                                              COMMENT '收件人类型：to/cc/bcc',
    email_address   VARCHAR(255)    NOT NULL                                              COMMENT '收件人邮箱地址',
    display_name    VARCHAR(255)                                                          COMMENT '收件人显示名称',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT fk_recipient_message  FOREIGN KEY (message_id) REFERENCES mail_message (id) ON DELETE CASCADE,
    CONSTRAINT chk_recipient_type    CHECK (type IN ('to', 'cc', 'bcc')),
    INDEX       idx_recipient_message   (message_id),
    INDEX       idx_recipient_email     (email_address),
    INDEX       idx_recipient_type      (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='邮件收件人表';

-- ============================================================================
-- 8. mail_attachment — 邮件附件表
-- ============================================================================
CREATE TABLE mail_attachment (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id         BIGINT          NOT NULL                                              COMMENT '所属用户ID',
    message_id      BIGINT                                                                COMMENT '所属邮件ID（草稿附件可为NULL）',
    original_name   VARCHAR(255)    NOT NULL                                              COMMENT '原始文件名',
    content_type    VARCHAR(128)                                                          COMMENT 'MIME类型',
    size_bytes      BIGINT          NOT NULL                                              COMMENT '文件大小（字节）',
    storage_type    VARCHAR(32)     NOT NULL                                              COMMENT '存储方式：local/minio',
    storage_path    VARCHAR(512)    NOT NULL                                              COMMENT '存储路径或对象键',
    checksum        VARCHAR(128)                                                          COMMENT '文件校验和（SHA-256）',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT fk_attachment_user     FOREIGN KEY (user_id)    REFERENCES sys_user (id)      ON DELETE CASCADE,
    CONSTRAINT fk_attachment_message  FOREIGN KEY (message_id) REFERENCES mail_message (id) ON DELETE SET NULL,
    CONSTRAINT chk_attachment_storage CHECK (storage_type IN ('local', 'minio')),
    INDEX       idx_attachment_user    (user_id),
    INDEX       idx_attachment_message (message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='邮件附件表';

-- ============================================================================
-- 9. contact — 联系人表
-- ============================================================================
CREATE TABLE contact (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id         BIGINT          NOT NULL                                              COMMENT '所属用户ID',
    name            VARCHAR(128)    NOT NULL                                              COMMENT '联系人姓名',
    email_address   VARCHAR(255)    NOT NULL                                              COMMENT '联系人邮箱',
    phone           VARCHAR(64)                                                           COMMENT '联系电话',
    company         VARCHAR(128)                                                          COMMENT '公司名称',
    department      VARCHAR(128)                                                          COMMENT '部门名称',
    remark          VARCHAR(512)                                                          COMMENT '备注',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
                                    ON UPDATE CURRENT_TIMESTAMP(3)                        COMMENT '更新时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记',
    CONSTRAINT uk_contact_user_email    UNIQUE KEY (user_id, email_address),
    CONSTRAINT fk_contact_user          FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE CASCADE,
    INDEX       idx_contact_user    (user_id),
    INDEX       idx_contact_name    (name),
    INDEX       idx_contact_email   (email_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='联系人表';

-- ============================================================================
-- 10. login_audit — 登录审计表 (仅created_at，无updated_at)
-- ============================================================================
CREATE TABLE login_audit (
    id              BIGINT          PRIMARY KEY AUTO_INCREMENT                           COMMENT '主键ID',
    user_id         BIGINT                                                                COMMENT '用户ID（登录失败时可为NULL）',
    username        VARCHAR(64)                                                           COMMENT '尝试登录的用户名',
    ip_address      VARCHAR(64)                                                           COMMENT '客户端IP地址',
    user_agent      VARCHAR(512)                                                          COMMENT '客户端User-Agent',
    success         TINYINT(1)      NOT NULL                                              COMMENT '登录结果：1=成功 0=失败',
    reason          VARCHAR(255)                                                          COMMENT '失败原因（如：密码错误/账号禁用）',
    created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3)                 COMMENT '创建时间',
    deleted         TINYINT(1)      NOT NULL DEFAULT 0                                    COMMENT '软删除标记（GDPR数据清除）',
    CONSTRAINT fk_login_audit_user   FOREIGN KEY (user_id) REFERENCES sys_user (id) ON DELETE SET NULL,
    INDEX       idx_login_audit_user          (user_id),
    INDEX       idx_login_audit_created_at    (created_at),
    INDEX       idx_login_audit_success       (success),
    INDEX       idx_login_audit_ip            (ip_address),
    INDEX       idx_login_audit_user_time     (user_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='登录审计表';

-- ============================================================================
-- Seed Data — 默认角色
-- ============================================================================
INSERT INTO sys_role (code, name, description) VALUES
    ('admin', '管理员', '系统管理员，拥有全部权限'),
    ('user',  '普通用户', '普通用户，拥有基本功能权限')
ON DUPLICATE KEY UPDATE name = VALUES(name);
