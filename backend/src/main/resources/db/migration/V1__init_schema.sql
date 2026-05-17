CREATE TABLE IF NOT EXISTS sys_user (
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

CREATE TABLE IF NOT EXISTS sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  UNIQUE KEY uk_user_role (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS mail_account (
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

CREATE TABLE IF NOT EXISTS mail_folder (
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

CREATE TABLE IF NOT EXISTS mail_message (
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

CREATE TABLE IF NOT EXISTS mail_recipient (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  message_id BIGINT NOT NULL,
  type VARCHAR(16) NOT NULL,
  email_address VARCHAR(255) NOT NULL,
  display_name VARCHAR(255),
  KEY idx_recipient_message (message_id),
  KEY idx_recipient_email (email_address)
);

CREATE TABLE IF NOT EXISTS mail_attachment (
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

CREATE TABLE IF NOT EXISTS contact (
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

CREATE TABLE IF NOT EXISTS login_audit (
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
