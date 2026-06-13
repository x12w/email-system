-- ============================================================
-- 邮件系统 · MySQL 数据库初始化脚本
-- ============================================================

-- -----------------------------------------------------------
-- 1. 用户表（系统用户，用于登录认证）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,          -- 登录用户名
  password_hash VARCHAR(255) NOT NULL,            -- 密码哈希（不可逆）
  display_name VARCHAR(64) NOT NULL,              -- 显示昵称
  email VARCHAR(255),                             -- 用户邮箱（可选）
  status TINYINT NOT NULL DEFAULT 1,              -- 1=正常 0=禁用
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0              -- 逻辑删除：1=已删除 0=正常
);

-- -----------------------------------------------------------
-- 2. 角色表（RBAC 角色定义）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,               -- 角色编码（如 admin / user）
  name VARCHAR(64) NOT NULL,                      -- 角色显示名
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------
-- 3. 用户-角色关联表（多对多）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  UNIQUE KEY uk_user_role (user_id, role_id)      -- 防止重复绑定
);

-- -----------------------------------------------------------
-- 4. 邮件账号表（用户绑定的外部邮箱，如 Gmail / 企业邮箱）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  display_name VARCHAR(128),
  smtp_host VARCHAR(255) NOT NULL,                -- 发件服务器地址
  smtp_port INT NOT NULL,                         -- 发件服务器端口
  smtp_ssl TINYINT NOT NULL DEFAULT 1,            -- 1=SSL/TLS 0=明文
  imap_host VARCHAR(255),                         -- 收件服务器地址
  imap_port INT,                                  -- 收件服务器端口
  imap_ssl TINYINT NOT NULL DEFAULT 1,
  auth_username VARCHAR(255) NOT NULL,            -- 认证用户名（通常等于邮箱）
  auth_password_encrypted VARCHAR(512) NOT NULL,  -- 加密后的认证密码
  status TINYINT NOT NULL DEFAULT 1,              -- 1=启用 0=停用
  last_sync_at DATETIME,                          -- 上次同步时间
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  KEY idx_mail_account_user (user_id)
);

-- -----------------------------------------------------------
-- 5. 邮件文件夹表（收件箱 / 已发送 / 草稿箱 等）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_folder (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,                     -- 本地显示名
  remote_name VARCHAR(255),                       -- 远程 IMAP 文件夹名
  type VARCHAR(32) NOT NULL,                      -- inbox / sent / draft / trash / custom
  unread_count INT NOT NULL DEFAULT 0,
  total_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_folder_account_remote (account_id, remote_name),
  KEY idx_mail_folder_user (user_id)
);

-- -----------------------------------------------------------
-- 6. 邮件消息表（核心：存储邮件主体内容）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_message (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  folder_id BIGINT,                                -- 所属文件夹
  message_uid VARCHAR(255),                        -- IMAP UID（服务器端唯一标识）
  message_id VARCHAR(512),                         -- RFC 5322 Message-ID 头
  from_address VARCHAR(255) NOT NULL,              -- 发件人地址
  from_name VARCHAR(255),                          -- 发件人名称
  subject VARCHAR(512),                            -- 邮件主题
  content_type VARCHAR(32) NOT NULL DEFAULT 'html',-- html / text
  content MEDIUMTEXT,                              -- 邮件正文（最大约 16MB）
  preview VARCHAR(512),                            -- 正文预览摘要
  sent_at DATETIME,                                -- 发件时间
  received_at DATETIME,                            -- 收件时间
  read_flag TINYINT NOT NULL DEFAULT 0,            -- 0=未读 1=已读
  star_flag TINYINT NOT NULL DEFAULT 0,            -- 0=未星标 1=已星标
  draft_flag TINYINT NOT NULL DEFAULT 0,           -- 0=正常邮件 1=草稿
  deleted_flag TINYINT NOT NULL DEFAULT 0,         -- 0=正常 1=已删除
  attachment_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_account_message_uid (account_id, message_uid),
  KEY idx_message_user_folder_time (user_id, folder_id, received_at),
  KEY idx_message_subject (subject)
);

-- -----------------------------------------------------------
-- 7. 邮件收件人表（TO / CC / BCC 关系）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_recipient (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  message_id BIGINT NOT NULL,
  type VARCHAR(16) NOT NULL,                       -- to / cc / bcc
  email_address VARCHAR(255) NOT NULL,
  display_name VARCHAR(255),
  KEY idx_recipient_message (message_id),
  KEY idx_recipient_email (email_address)
);

-- -----------------------------------------------------------
-- 8. 邮件附件表
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_attachment (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message_id BIGINT,                               -- NULL = 未关联消息的附件（如草稿中的）
  original_name VARCHAR(255) NOT NULL,             -- 原始文件名
  content_type VARCHAR(128),                       -- MIME 类型
  size_bytes BIGINT NOT NULL,
  storage_type VARCHAR(32) NOT NULL,               -- local / minio / s3
  storage_path VARCHAR(512) NOT NULL,              -- 存储路径或对象 key
  checksum VARCHAR(128),                           -- SHA-256 校验值，用于去重与完整性校验
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  KEY idx_attachment_user (user_id),
  KEY idx_attachment_message (message_id)
);

-- -----------------------------------------------------------
-- 9. 邮件智能分析结果表（AI/规则引擎处理后的标记）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_intelligence_result (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message_id BIGINT NOT NULL,
  spam_label VARCHAR(32) NOT NULL DEFAULT 'unknown',   -- spam / ham / unknown
  spam_score DECIMAL(5,4) NOT NULL DEFAULT 0,          -- 垃圾评分 0.0000 ~ 1.0000
  priority_label VARCHAR(32) NOT NULL DEFAULT 'normal',-- high / normal / low
  priority_score DECIMAL(5,4) NOT NULL DEFAULT 0,
  risk_level VARCHAR(32) NOT NULL DEFAULT 'none',      -- high / medium / low / none
  risk_score DECIMAL(5,4) NOT NULL DEFAULT 0,
  action_json JSON,                                    -- 建议操作（JSON）
  reason_json JSON,                                    -- 分析理由（JSON）
  plugin_name VARCHAR(128) NOT NULL,                   -- 执行分析的插件名
  plugin_version VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'success',       -- success / error
  error_message VARCHAR(512),
  analyzed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_intelligence_message (message_id),     -- 一封邮件只分析一次
  KEY idx_intelligence_user_priority (user_id, priority_label),
  KEY idx_intelligence_user_risk (user_id, risk_level),
  KEY idx_intelligence_user_spam (user_id, spam_label)
);

-- -----------------------------------------------------------
-- 10. 威胁指标表（钓鱼链接 / 恶意附件等安全标记）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_threat_indicator (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message_id BIGINT NOT NULL,
  intelligence_result_id BIGINT NOT NULL,          -- 关联的分析结果
  type VARCHAR(32) NOT NULL,                       -- suspicious_link / malicious_attachment / spoofing
  value VARCHAR(1024) NOT NULL,                    -- 具体内容（URL / 文件名 / header）
  risk_level VARCHAR(32) NOT NULL,                 -- high / medium / low
  reason VARCHAR(512),                             -- 标记原因
  rule_id VARCHAR(128),                            -- 触发规则 ID
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_threat_message (message_id),
  KEY idx_threat_user_risk (user_id, risk_level),
  KEY idx_threat_type (type)
);

-- -----------------------------------------------------------
-- 11. 推送事件表（新邮件通知 / 安全告警等用户通知）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS mail_push_event (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message_id BIGINT NOT NULL,
  event_type VARCHAR(64) NOT NULL,                 -- new_mail / security_alert / reminder
  title VARCHAR(255) NOT NULL,
  content VARCHAR(512),
  priority VARCHAR(32) NOT NULL DEFAULT 'normal',  -- high / normal / low
  read_flag TINYINT NOT NULL DEFAULT 0,            -- 0=未读 1=已读
  pushed_at DATETIME,                              -- 推送时间
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_push_user_read_time (user_id, read_flag, created_at),
  KEY idx_push_message (message_id)
);

-- -----------------------------------------------------------
-- 12. 智能插件表（插件注册与版本管理）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS intelligence_plugin (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  version VARCHAR(64) NOT NULL,
  runtime VARCHAR(32) NOT NULL DEFAULT 'python-native', -- python-native / wasm / grpc
  artifact_path VARCHAR(512) NOT NULL,                  -- 插件包存储路径
  checksum VARCHAR(128),                                -- 插件包校验值，防篡改
  enabled TINYINT NOT NULL DEFAULT 1,
  timeout_ms INT NOT NULL DEFAULT 2000,                 -- 单次分析超时（毫秒）
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_plugin_name_version (name, version)
);

-- -----------------------------------------------------------
-- 13. 联系人表（用户个人通讯录）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  phone VARCHAR(64),
  remark VARCHAR(512),                                  -- 备注
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_contact_user_email (user_id, email_address)
);

-- -----------------------------------------------------------
-- 14. 登录审计表（记录每次登录尝试，安全审计用）
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS login_audit (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT,
  username VARCHAR(64),
  ip_address VARCHAR(64),
  user_agent VARCHAR(512),
  success TINYINT NOT NULL,                             -- 1=成功 0=失败
  reason VARCHAR(255),                                  -- 失败原因
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_login_audit_user_time (user_id, created_at)
);
