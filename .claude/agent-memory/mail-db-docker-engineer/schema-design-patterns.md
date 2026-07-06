---
name: schema-design-patterns
description: Database schema conventions, index naming patterns, and FK constraint decisions for the email system MySQL 8.0 schema
metadata:
  type: reference
---

## Schema Conventions

- **Database:** `email_system`, charset `utf8mb4`, collation `utf8mb4_0900_ai_ci`
- **Engine:** InnoDB on all tables
- **Datetime precision:** `DATETIME(3)` for millisecond precision on all timestamp columns
- **Soft delete:** Every table (except login_audit) has `deleted TINYINT(1) NOT NULL DEFAULT 0`
- **Timestamps:** Every table has `created_at` and `updated_at` with `DEFAULT CURRENT_TIMESTAMP(3)` and `ON UPDATE CURRENT_TIMESTAMP(3)` — except `login_audit` which only has `created_at` (audit log rows are immutable)
- **Booleans:** Modeled as `TINYINT(1)` — 0=false, 1=true
- **Status fields:** `TINYINT(1)` — 1=enabled, 0=disabled

## Index Naming Convention

- Unique keys: `uk_{short_table}_{field}` (e.g., `uk_user_username`, `uk_folder_account_remote`)
- Non-unique indexes: `idx_{short_table}_{field}` (e.g., `idx_message_read_flag`, `idx_contact_name`)
- FK constraint names: `fk_{child_table}_{parent_table}` (e.g., `fk_message_user`, `fk_folder_account`)
- CHECK constraint names: `chk_{table}_{column}` (e.g., `chk_folder_type`, `chk_attachment_storage`)

## FIELD VALUE CONSTRAINTS

- `mail_folder.type`: ENUM in CHECK — `'inbox','sent','draft','trash','spam','custom'`
- `mail_recipient.type`: ENUM in CHECK — `'to','cc','bcc'`
- `mail_attachment.storage_type`: ENUM in CHECK — `'local','minio'`
- `sys_user.status`: application-enforced — 1=enabled, 0=disabled

## FK CASCADE RULES

- Most child tables: `ON DELETE CASCADE` (user deleted → all owned data deleted)
- Nullable FKs for entities that can outlive their parent:
  - `mail_message.folder_id` → `ON DELETE SET NULL` (message stays accessible if folder is deleted)
  - `mail_attachment.message_id` → `ON DELETE SET NULL` (attachment metadata survives if message is deleted, for draft reattachment)
  - `login_audit.user_id` → `ON DELETE SET NULL` (audit trail preserved even if user is purged)

## Seed Data

Two default roles inserted with `ON DUPLICATE KEY UPDATE`:
- `code='admin'`, `name='管理员'`
- `code='user'`, `name='普通用户'`

## Key Differences from Flyway Migration (V1__init_schema.sql)

The `data/mysql/01-init-schema.sql` is a production-enhanced version of the Flyway migration with:
1. `DATETIME(3)` instead of `DATETIME` everywhere
2. Full FOREIGN KEY constraints
3. CHECK constraints on enum-like VARCHAR columns
4. All columns have COMMENT annotations
5. Indexes on flag columns for query optimization (read_flag, deleted_flag, success)
6. Additional fields: sys_user.avatar_url, sys_user.last_login_at, sys_user.last_login_ip, sys_role.description, contact.company, contact.department, mail_message.size_bytes
7. Seed data for default roles
