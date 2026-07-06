ALTER TABLE mail_message ADD COLUMN headers TEXT COMMENT '邮件头集合（JSON 格式）' AFTER attachment_count;
