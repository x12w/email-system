# 数据库设计草案

数据库：MySQL 8.0，字符集建议 `utf8mb4`，排序规则建议 `utf8mb4_0900_ai_ci`。

## 表清单

| 表名 | 说明 |
| --- | --- |
| `sys_user` | 系统用户 |
| `sys_role` | 角色 |
| `sys_user_role` | 用户角色关系 |
| `mail_account` | 用户绑定的邮箱账号 |
| `mail_folder` | 邮件文件夹 |
| `mail_message` | 邮件主表 |
| `mail_recipient` | 邮件收件人、抄送、密送 |
| `mail_attachment` | 附件元数据 |
| `contact` | 联系人 |
| `login_audit` | 登录审计 |

## 建表 SQL 初稿

```sql
CREATE TABLE sys_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(64) NOT NULL,
  email VARCHAR(255),
  status TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0
);

CREATE TABLE sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  UNIQUE KEY uk_user_role (user_id, role_id)
);

CREATE TABLE mail_account (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  display_name VARCHAR(128),
  smtp_host VARCHAR(255) NOT NULL,
  smtp_port INT NOT NULL,
  smtp_ssl TINYINT NOT NULL DEFAULT 1,
  imap_host VARCHAR(255),
  imap_port INT,
  imap_ssl TINYINT NOT NULL DEFAULT 1,
  auth_username VARCHAR(255) NOT NULL,
  auth_password_encrypted VARCHAR(512) NOT NULL,
  status TINYINT NOT NULL DEFAULT 1,
  last_sync_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  KEY idx_mail_account_user (user_id)
);

CREATE TABLE mail_folder (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  remote_name VARCHAR(255),
  type VARCHAR(32) NOT NULL,
  unread_count INT NOT NULL DEFAULT 0,
  total_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_folder_account_remote (account_id, remote_name),
  KEY idx_mail_folder_user (user_id)
);

CREATE TABLE mail_message (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  folder_id BIGINT,
  message_uid VARCHAR(255),
  message_id VARCHAR(512),
  from_address VARCHAR(255) NOT NULL,
  from_name VARCHAR(255),
  subject VARCHAR(512),
  content_type VARCHAR(32) NOT NULL DEFAULT 'html',
  content MEDIUMTEXT,
  preview VARCHAR(512),
  sent_at DATETIME,
  received_at DATETIME,
  read_flag TINYINT NOT NULL DEFAULT 0,
  star_flag TINYINT NOT NULL DEFAULT 0,
  draft_flag TINYINT NOT NULL DEFAULT 0,
  deleted_flag TINYINT NOT NULL DEFAULT 0,
  attachment_count INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_account_message_uid (account_id, message_uid),
  KEY idx_message_user_folder_time (user_id, folder_id, received_at),
  KEY idx_message_subject (subject)
);

CREATE TABLE mail_recipient (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  message_id BIGINT NOT NULL,
  type VARCHAR(16) NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  display_name VARCHAR(255),
  KEY idx_recipient_message (message_id),
  KEY idx_recipient_email (email_address)
);

CREATE TABLE mail_attachment (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  message_id BIGINT,
  original_name VARCHAR(255) NOT NULL,
  content_type VARCHAR(128),
  size_bytes BIGINT NOT NULL,
  storage_type VARCHAR(32) NOT NULL,
  storage_path VARCHAR(512) NOT NULL,
  checksum VARCHAR(128),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  KEY idx_attachment_user (user_id),
  KEY idx_attachment_message (message_id)
);

CREATE TABLE contact (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  name VARCHAR(128) NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  phone VARCHAR(64),
  remark VARCHAR(512),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_contact_user_email (user_id, email_address)
);

CREATE TABLE login_audit (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT,
  username VARCHAR(64),
  ip_address VARCHAR(64),
  user_agent VARCHAR(512),
  success TINYINT NOT NULL,
  reason VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_login_audit_user_time (user_id, created_at)
);
```

## 字段约定

- 主键统一使用 `BIGINT AUTO_INCREMENT`，后续可切换雪花 ID。
- 软删除字段统一为 `deleted`。
- 状态字段：`1` 表示启用，`0` 表示禁用。
- 收件人类型：`to`、`cc`、`bcc`。
- 文件夹类型：`inbox`、`sent`、`draft`、`trash`、`spam`、`custom`。
- 附件 `storage_type`：`local` 或 `minio`。

