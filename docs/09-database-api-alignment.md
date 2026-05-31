# 数据库前后端协同对齐接口文档

> 本文档用于统一前后端对数据库字段的理解，确保 API JSON 字段与数据库列精确对齐。

## 1. 概述

### 1.1 文档目的

项目目前已有完整的数据库表设计（[V1__init_schema.sql](../backend/src/main/resources/db/migration/V1__init_schema.sql) + [V2__create_full_tables.sql](../backend/src/main/resources/db/migration/V2__create_full_tables.sql)，共 14 张表）和 API 接口清单（[03-frontend-backend-contract.md](03-frontend-backend-contract.md)，共 32 个端点），但缺少一份将两者精确对齐的协同文档。本文档填补这一空白，确保前后端开发时字段命名、类型、校验规则保持一致。

### 1.2 引用依赖

| 依赖文档 | 用途 |
|----------|------|
| [V1__init_schema.sql](../backend/src/main/resources/db/migration/V1__init_schema.sql) + [V2__create_full_tables.sql](../backend/src/main/resources/db/migration/V2__create_full_tables.sql) | 数据库表结构权威来源 |
| [03-frontend-backend-contract.md](03-frontend-backend-contract.md) | API 端点与响应格式规范 |
| [08-redis-cache-design.md](08-redis-cache-design.md) | Redis 缓存结构与字段定义 |

### 1.3 数据库表总览

| # | 表名 | 中文名称 | API 暴露方式 |
|---|------|----------|-------------|
| 1 | `sys_user` | 系统用户表 | `/api/auth/*` 接口 |
| 2 | `sys_role` | 角色表 | 内嵌在用户信息/会话中 |
| 3 | `sys_user_role` | 用户角色关联表 | 内部关联，不直接暴露 |
| 4 | `mail_account` | 邮箱账号表 | `/api/mail-accounts/*` 接口 |
| 5 | `mail_folder` | 邮件文件夹表 | `/api/folders/*` 接口 |
| 6 | `mail_message` | 邮件主表 | `/api/messages/*` 接口 |
| 7 | `mail_recipient` | 邮件收件人表 | 内嵌在邮件详情/发送接口 |
| 8 | `mail_attachment` | 邮件附件表 | `/api/attachments/*` 接口 |
| 9 | `mail_intelligence_result` | 智能分析结果表 | `/api/intelligence/*` 接口（规划中） |
| 10 | `mail_threat_indicator` | 威胁指标记录表 | 内嵌在智能分析结果中 |
| 11 | `mail_push_event` | 高优先级推送记录表 | `/api/push-events/*` 接口（规划中） |
| 12 | `intelligence_plugin` | 智能插件注册表 | `/api/intelligence/plugins/*` 接口（规划中） |
| 13 | `contact` | 联系人表 | `/api/contacts/*` 接口 |
| 14 | `login_audit` | 登录审计表 | 内部记录，不直接暴露 API |

---

## 2. 命名与类型映射规范

### 2.1 命名转换规则

| 层级 | 命名风格 | 示例 |
|------|---------|------|
| 数据库列名 | `snake_case` | `display_name`、`created_at`、`read_flag` |
| API JSON 字段 | `camelCase` | `displayName`、`createdAt`、`readFlag` |
| Java 实体属性 | `camelCase` | `displayName`、`createdAt`、`readFlag` |

后端使用 MyBatis-Plus 的 `map-underscore-to-camel-case: true` 自动完成转换。

### 2.2 数据库类型 → JSON 类型映射

| 数据库类型 | JSON 类型 | 说明 |
|-----------|----------|------|
| `BIGINT` | `number` | 主键 ID、外键、计数器 |
| `INT` | `number` | 端口号、排序序号、计数 |
| `TINYINT(1)` | `boolean` | 标志位字段（0=false, 1=true） |
| `VARCHAR(N)` | `string` | 变长字符串 |
| `TEXT` / `MEDIUMTEXT` | `string` | 长文本 |
| `DATETIME(3)` | `string`（ISO 8601） | 毫秒精度时间，格式 `2026-05-17T22:30:00+08:00` |
| `DECIMAL` | `number` | 小数/浮点值 |

### 2.3 通用字段约定

所有表均包含以下通用字段，API 响应中的处理规则如下：

| DB 列 | API 字段 | 响应中是否包含 | 说明 |
|-------|---------|---------------|------|
| `id` | `id` | 是 | 主键，响应中转为 `number` |
| `created_at` | `createdAt` | 是 | 创建时间，ISO 8601 格式 |
| `updated_at` | `updatedAt` | 是 | 更新时间，ISO 8601 格式 |
| `deleted` | — | **不暴露** | 软删除标记，仅后端逻辑使用 |

---

## 3. 表-API 字段对照

### 3.1 sys_user — 系统用户表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/auth/login` | 登录，此接口不直接映射表字段 |
| `POST` | `/api/auth/refresh` | 刷新 Token，不涉及表字段 |
| `POST` | `/api/auth/logout` | 退出登录，不涉及表字段 |
| `GET` | `/api/auth/me` | 获取当前用户信息 |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 用户主键 |
| `username` | `VARCHAR(64)` | 是 | `username` | `string` | 用户名，唯一 |
| `password_hash` | `VARCHAR(255)` | 是 | — | — | **绝不暴露给前端** |
| `display_name` | `VARCHAR(64)` | 是 | `displayName` | `string` | 显示名称 |
| `email` | `VARCHAR(255)` | 否 | `email` | `string` | 恢复/通知邮箱 |
| `avatar_url` | `VARCHAR(512)` | 否 | `avatarUrl` | `string` | 头像 URL |
| `status` | `TINYINT(1)` | 是 | `status` | `number` | 1=启用，0=禁用（见 4.1） |
| `last_login_at` | `DATETIME(3)` | 否 | `lastLoginAt` | `string` | 最后登录时间 |
| `last_login_ip` | `VARCHAR(64)` | 否 | — | — | 不暴露给前端（隐私） |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 注册时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

**登录响应（含角色信息）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
    "expiresIn": 7200,
    "user": {
      "id": 1,
      "username": "admin",
      "displayName": "管理员",
      "email": "admin@example.com",
      "avatarUrl": "https://cdn.example.com/avatars/1.jpg",
      "status": 1,
      "lastLoginAt": "2026-05-17T08:30:00+08:00",
      "createdAt": "2026-01-15T10:00:00+08:00",
      "roles": ["admin"],
      "permissions": ["mail:read", "mail:send", "contact:read", "contact:write"]
    }
  }
}
```

**当前用户信息响应（GET /api/auth/me）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "id": 1,
    "username": "admin",
    "displayName": "管理员",
    "email": "admin@example.com",
    "avatarUrl": "https://cdn.example.com/avatars/1.jpg",
    "status": 1,
    "lastLoginAt": "2026-05-17T08:30:00+08:00",
    "createdAt": "2026-01-15T10:00:00+08:00",
    "roles": ["admin"],
    "permissions": ["mail:read", "mail:send", "contact:read", "contact:write"]
  }
}
```

**Redis 缓存对应：** `session:user:{user_id}` → 值 JSON 包含 `user_id`、`username`、`display_name`、`email`、`avatar_url`、`status`、`roles`、`permissions`

**校验规则：**
- `username`：长度 3-64，仅允许字母、数字和下划线
- `display_name`：长度 1-64，不允许为空
- `email`：合法的邮箱格式，可为空

---

### 3.2 sys_role — 角色表

**关联 API：** 无独立端点，角色信息通过 `/api/auth/login` 和 `/api/auth/me` 中的 `roles` 字段内嵌返回。

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | — | — | 不暴露 |
| `code` | `VARCHAR(64)` | 是 | （内嵌在 roles[] 中） | `string` | 角色编码，如 `admin`、`user` |
| `name` | `VARCHAR(64)` | 是 | — | — | 仅后端使用 |
| `description` | `VARCHAR(255)` | 否 | — | — | 仅后端使用 |

**前端的角色编码直接来自 `sys_role.code`：**
- `admin` — 管理员，拥有全部权限
- `user` — 普通用户，拥有基本功能权限

**种子数据（来自 V2 迁移脚本）：**

```sql
INSERT INTO sys_role (code, name, description) VALUES
    ('admin', '管理员', '系统管理员，拥有全部权限'),
    ('user',  '普通用户', '普通用户，拥有基本功能权限');
```

---

### 3.3 sys_user_role — 用户角色关联表

**关联 API：** 无。该表为内部多对多关联，数据通过 JOIN 查询后在 `roles` 数组中暴露。

**字段说明：**

| DB 列 | DB 类型 | 说明 |
|-------|---------|------|
| `id` | `BIGINT` | 主键 |
| `user_id` | `BIGINT` | 关联 `sys_user.id`（CASCADE） |
| `role_id` | `BIGINT` | 关联 `sys_role.id`（CASCADE） |

> 前端无需关心此表的存在，后端通过 JOIN 查询将角色编码聚合为 `roles: ["admin"]` 格式返回。

---

### 3.4 mail_account — 邮箱账号表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/mail-accounts` | 获取当前用户的邮箱账号列表 |
| `POST` | `/api/mail-accounts` | 新增邮箱账号 |
| `PUT` | `/api/mail-accounts/{id}` | 更新邮箱账号 |
| `DELETE` | `/api/mail-accounts/{id}` | 删除邮箱账号 |
| `POST` | `/api/mail-accounts/{id}/test` | 测试 SMTP/IMAP 配置 |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 账号主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取，不暴露 |
| `email_address` | `VARCHAR(255)` | 是 | `emailAddress` | `string` | 邮箱地址 |
| `display_name` | `VARCHAR(128)` | 否 | `displayName` | `string` | 发件显示名称 |
| `smtp_host` | `VARCHAR(255)` | 是 | `smtpHost` | `string` | SMTP 服务器地址 |
| `smtp_port` | `INT` | 是 | `smtpPort` | `number` | SMTP 端口 |
| `smtp_ssl` | `TINYINT(1)` | 是 | `smtpSsl` | `boolean` | SMTP 是否启用 SSL |
| `imap_host` | `VARCHAR(255)` | 否 | `imapHost` | `string` | IMAP 服务器地址 |
| `imap_port` | `INT` | 否 | `imapPort` | `number` | IMAP 端口 |
| `imap_ssl` | `TINYINT(1)` | 是 | `imapSsl` | `boolean` | IMAP 是否启用 SSL |
| `auth_username` | `VARCHAR(255)` | 是 | `authUsername` | `string` | 认证用户名 |
| `auth_password_encrypted` | `VARCHAR(512)` | 是 | `authPassword` | `string` | **仅写入时接收**，响应中脱敏为 `"******"` |
| `status` | `TINYINT(1)` | 是 | `status` | `number` | 1=启用，0=禁用 |
| `last_sync_at` | `DATETIME(3)` | 否 | `lastSyncAt` | `string` | 最后同步时间 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

**列表响应示例（GET /api/mail-accounts）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": [
    {
      "id": 1,
      "emailAddress": "zhangsan@example.com",
      "displayName": "张三",
      "smtpHost": "smtp.example.com",
      "smtpPort": 465,
      "smtpSsl": true,
      "imapHost": "imap.example.com",
      "imapPort": 993,
      "imapSsl": true,
      "authUsername": "zhangsan@example.com",
      "authPassword": "******",
      "status": 1,
      "lastSyncAt": "2026-05-17T08:30:00+08:00",
      "createdAt": "2026-01-15T10:00:00+08:00",
      "updatedAt": "2026-05-17T08:30:00+08:00"
    }
  ]
}
```

**新增/更新请求示例（POST/PUT /api/mail-accounts）：**

```json
{
  "emailAddress": "zhangsan@example.com",
  "displayName": "张三",
  "smtpHost": "smtp.example.com",
  "smtpPort": 465,
  "smtpSsl": true,
  "imapHost": "imap.example.com",
  "imapPort": 993,
  "imapSsl": true,
  "authUsername": "zhangsan@example.com",
  "authPassword": "plain-text-password"
}
```

**校验规则：**
- `emailAddress`：必填，合法邮箱格式
- `smtpHost`：必填，合法域名或 IP 地址
- `smtpPort`：必填，范围 1-65535
- `authUsername`：必填，长度不少于 1
- `authPassword`：新增时必填，更新时可选（留空表示不修改密码）

---

### 3.5 mail_folder — 邮件文件夹表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/folders` | 获取文件夹列表及未读数 |
| `POST` | `/api/folders/sync` | 同步远程文件夹 |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 文件夹主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `account_id` | `BIGINT` | 是 | `accountId` | `number` | 所属账号 ID |
| `name` | `VARCHAR(128)` | 是 | `name` | `string` | 文件夹显示名称 |
| `remote_name` | `VARCHAR(255)` | 否 | `remoteName` | `string` | 远程文件夹原始名称 |
| `type` | `VARCHAR(32)` | 是 | `type` | `string` | 文件夹类型（见 4.2） |
| `unread_count` | `INT` | 是 | `unreadCount` | `number` | 未读邮件数 |
| `total_count` | `INT` | 是 | `totalCount` | `number` | 邮件总数 |
| `sort_order` | `INT` | 是 | `sortOrder` | `number` | 排序序号 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

**列表响应示例（GET /api/folders）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": [
    {
      "id": 5,
      "accountId": 1,
      "name": "收件箱",
      "remoteName": "INBOX",
      "type": "inbox",
      "unreadCount": 12,
      "totalCount": 245,
      "sortOrder": 1,
      "createdAt": "2026-01-15T10:00:00+08:00",
      "updatedAt": "2026-05-17T08:30:00+08:00"
    },
    {
      "id": 7,
      "accountId": 1,
      "name": "已发送",
      "remoteName": "Sent",
      "type": "sent",
      "unreadCount": 0,
      "totalCount": 89,
      "sortOrder": 2,
      "createdAt": "2026-01-15T10:00:00+08:00",
      "updatedAt": "2026-05-17T08:30:00+08:00"
    },
    {
      "id": 9,
      "accountId": 1,
      "name": "草稿箱",
      "remoteName": "Drafts",
      "type": "draft",
      "unreadCount": 3,
      "totalCount": 3,
      "sortOrder": 3,
      "createdAt": "2026-01-15T10:00:00+08:00",
      "updatedAt": "2026-05-17T08:30:00+08:00"
    }
  ]
}
```

**Redis 缓存对应：**
- `mail:folder:stats:{user_id}` → Hash，field=`folder_id`，value=JSON `{"total_count":N,"unread_count":N,"name":"...","type":"..."}`
- `mail:unread:counts:{user_id}` → Hash，field=`folder_id`，value=未读数

---

### 3.6 mail_message — 邮件主表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/messages` | 邮件列表（分页、筛选） |
| `GET` | `/api/messages/{id}` | 邮件详情 |
| `POST` | `/api/messages/send` | 发送邮件 |
| `POST` | `/api/messages/drafts` | 保存草稿 |
| `PUT` | `/api/messages/{id}/read` | 标记已读/未读 |
| `DELETE` | `/api/messages/{id}` | 删除邮件（移入回收站） |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 邮件主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `account_id` | `BIGINT` | 是 | `accountId` | `number` | 所属账号 ID |
| `folder_id` | `BIGINT` | 否 | `folderId` | `number` | 当前所在文件夹 ID |
| `message_uid` | `VARCHAR(255)` | 否 | `messageUid` | `string` | IMAP 消息 UID |
| `message_id` | `VARCHAR(512)` | 否 | `messageId` | `string` | RFC 5322 Message-ID 头 |
| `from_address` | `VARCHAR(255)` | 是 | `fromAddress` | `string` | 发件人邮箱地址 |
| `from_name` | `VARCHAR(255)` | 否 | `fromName` | `string` | 发件人显示名称 |
| `subject` | `VARCHAR(512)` | 否 | `subject` | `string` | 邮件主题 |
| `content_type` | `VARCHAR(32)` | 是 | `contentType` | `string` | 内容类型（见 4.6） |
| `content` | `MEDIUMTEXT` | 否 | `content` | `string` | 邮件正文（列表接口不返回） |
| `preview` | `VARCHAR(512)` | 否 | `preview` | `string` | 正文预览摘要（仅列表接口返回） |
| `sent_at` | `DATETIME(3)` | 否 | `sentAt` | `string` | 发件时间 |
| `received_at` | `DATETIME(3)` | 否 | `receivedAt` | `string` | 收件时间 |
| `size_bytes` | `BIGINT` | 是 | `sizeBytes` | `number` | 邮件大小（字节） |
| `read_flag` | `TINYINT(1)` | 是 | `readFlag` | `boolean` | 已读标记 |
| `star_flag` | `TINYINT(1)` | 是 | `starFlag` | `boolean` | 星标标记 |
| `draft_flag` | `TINYINT(1)` | 是 | `draftFlag` | `boolean` | 草稿标记 |
| `deleted_flag` | `TINYINT(1)` | 是 | `deletedFlag` | `boolean` | 回收站标记 |
| `attachment_count` | `INT` | 是 | `attachmentCount` | `number` | 附件数量 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

**邮件列表项响应（GET /api/messages，不含正文和收件人详情）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "records": [
      {
        "id": 5001,
        "accountId": 1,
        "folderId": 5,
        "messageUid": "14285",
        "messageId": "<20260517115500.abc@mail.example.com>",
        "fromAddress": "alice@example.com",
        "fromName": "Alice",
        "subject": "会议纪要",
        "preview": "大家好，以下是今天会议的总结...",
        "sentAt": "2026-05-17T11:55:00+08:00",
        "receivedAt": "2026-05-17T12:00:00+08:00",
        "sizeBytes": 24576,
        "readFlag": false,
        "starFlag": false,
        "draftFlag": false,
        "deletedFlag": false,
        "attachmentCount": 2,
        "createdAt": "2026-05-17T12:00:00+08:00",
        "updatedAt": "2026-05-17T12:00:00+08:00"
      }
    ],
    "page": 1,
    "size": 20,
    "total": 245
  }
}
```

**邮件详情响应（GET /api/messages/{id}，含正文、收件人和附件）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "id": 5001,
    "accountId": 1,
    "folderId": 5,
    "messageUid": "14285",
    "messageId": "<20260517115500.abc@mail.example.com>",
    "fromAddress": "alice@example.com",
    "fromName": "Alice",
    "subject": "会议纪要",
    "contentType": "html",
    "content": "<html><body><p>大家好，以下是今天会议的总结...</p></body></html>",
    "sentAt": "2026-05-17T11:55:00+08:00",
    "receivedAt": "2026-05-17T12:00:00+08:00",
    "sizeBytes": 24576,
    "readFlag": true,
    "starFlag": false,
    "draftFlag": false,
    "deletedFlag": false,
    "attachmentCount": 2,
    "attachments": [
      {
        "id": 201,
        "originalName": "会议纪要.pdf",
        "contentType": "application/pdf",
        "sizeBytes": 102400
      }
    ],
    "recipients": [
      {
        "type": "to",
        "emailAddress": "bob@example.com",
        "displayName": "Bob"
      },
      {
        "type": "cc",
        "emailAddress": "charlie@example.com",
        "displayName": "Charlie"
      }
    ],
    "createdAt": "2026-05-17T12:00:00+08:00",
    "updatedAt": "2026-05-17T12:00:00+08:00"
  }
}
```

**发送邮件请求（POST /api/messages/send）：**

```json
{
  "accountId": 1,
  "to": ["bob@example.com"],
  "cc": ["charlie@example.com"],
  "bcc": [],
  "subject": "会议纪要",
  "contentType": "html",
  "content": "<html><body><p>大家好...</p></body></html>",
  "attachmentIds": [201, 202]
}
```

> 发送请求中的 `to`/`cc`/`bcc` 与 `mail_recipient` 表对应，`attachmentIds` 与 `mail_attachment` 表对应。

**保存草稿请求（POST /api/messages/drafts）：**

```json
{
  "accountId": 1,
  "to": ["bob@example.com"],
  "cc": [],
  "bcc": [],
  "subject": "草稿邮件",
  "contentType": "html",
  "content": "<p>未完待续...</p>",
  "attachmentIds": []
}
```

> 草稿与发送请求格式一致。后端将 `draft_flag` 设为 1，`folder_id` 指向草稿文件夹。

**标记已读（PUT /api/messages/{id}/read）：**

```json
{
  "readFlag": true
}
```

**列表查询参数（GET /api/messages）：**

| 参数 | 类型 | 必填 | 对应 DB 列 | 说明 |
|------|------|------|-----------|------|
| `folderId` | `number` | 否 | `folder_id` | 按文件夹筛选 |
| `keyword` | `string` | 否 | `subject` + `from_address` + `from_name` | 全文搜索关键词 |
| `read` | `boolean` | 否 | `read_flag` | true=已读，false=未读 |
| `starred` | `boolean` | 否 | `star_flag` | 星标筛选 |
| `page` | `number` | 否 | — | 页码，从 1 开始，默认 1 |
| `size` | `number` | 否 | — | 每页条数，默认 20 |

**Redis 缓存对应：**
- `mail:message:list:{user_id}:{folder_id}` → 有序集合，member=邮件摘要 JSON（含 `id`、`subject`、`from_address`、`from_name`、`read_flag`、`star_flag`、`attachment_count`、`received_at`）
- `mail:message:detail:{message_id}` → 字符串 JSON，完整邮件数据（含 `content`、`attachments`、`recipients`）

---

### 3.7 mail_recipient — 邮件收件人表

**关联 API：** 无独立端点。收件人数据在以下接口中以内嵌数组形式出现：
- `GET /api/messages/{id}` — 邮件详情响应中内嵌 `recipients` 数组
- `POST /api/messages/send` — 发送请求中通过 `to`/`cc`/`bcc` 传入
- `POST /api/messages/drafts` — 草稿请求中通过 `to`/`cc`/`bcc` 传入

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | — | — | 不暴露 |
| `message_id` | `BIGINT` | 是 | — | — | 从邮件上下文获取 |
| `type` | `VARCHAR(16)` | 是 | `type` | `string` | 收件人类型（见 4.3） |
| `email_address` | `VARCHAR(255)` | 是 | `emailAddress` | `string` | 收件人邮箱 |
| `display_name` | `VARCHAR(255)` | 否 | `displayName` | `string` | 收件人显示名称 |

**发送请求中的格式（前端 → 后端）：**

```json
{
  "to": ["alice@example.com", "bob@example.com"],
  "cc": ["charlie@example.com"],
  "bcc": []
}
```

> 前端仅传邮箱地址字符串数组，后端负责拆分为 `mail_recipient` 记录并设置对应的 `type`。

**响应中的格式（后端 → 前端）：**

```json
{
  "recipients": [
    { "type": "to", "emailAddress": "bob@example.com", "displayName": "Bob" },
    { "type": "cc", "emailAddress": "charlie@example.com", "displayName": "Charlie" }
  ]
}
```

**Redis 缓存对应：** `mail:message:detail:{message_id}` 的 JSON 中内嵌 `recipients` 数组。

---

### 3.8 mail_attachment — 邮件附件表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/attachments` | 上传附件（multipart/form-data，字段名 `file`） |
| `GET` | `/api/attachments/{id}/download` | 下载附件 |
| `DELETE` | `/api/attachments/{id}` | 删除未关联邮件的附件 |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 附件主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `message_id` | `BIGINT` | 否 | `messageId` | `number` | 所属邮件 ID（草稿附件可为 null） |
| `original_name` | `VARCHAR(255)` | 是 | `originalName` | `string` | 原始文件名 |
| `content_type` | `VARCHAR(128)` | 否 | `contentType` | `string` | MIME 类型 |
| `size_bytes` | `BIGINT` | 是 | `sizeBytes` | `number` | 文件大小（字节） |
| `storage_type` | `VARCHAR(32)` | 是 | — | — | 存储方式，后端内部使用（见 4.4） |
| `storage_path` | `VARCHAR(512)` | 是 | — | — | 存储路径，后端内部使用 |
| `checksum` | `VARCHAR(128)` | 否 | — | — | SHA-256 校验和，后端内部使用 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 上传时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

**上传响应示例（POST /api/attachments）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "id": 201,
    "originalName": "会议纪要.pdf",
    "contentType": "application/pdf",
    "sizeBytes": 102400,
    "createdAt": "2026-05-17T12:00:00+08:00"
  }
}
```

**Redis 缓存对应：** `mail:message:detail:{message_id}` 的 JSON 中内嵌 `attachments` 数组（仅含 `id`、`original_name`、`size_bytes`、`content_type`）。

---

### 3.9 contact — 联系人表

**关联 API：**

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/contacts` | 联系人列表（支持分页和关键词搜索） |
| `POST` | `/api/contacts` | 新增联系人 |
| `PUT` | `/api/contacts/{id}` | 更新联系人 |
| `DELETE` | `/api/contacts/{id}` | 删除联系人 |

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 联系人主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `name` | `VARCHAR(128)` | 是 | `name` | `string` | 联系人姓名 |
| `email_address` | `VARCHAR(255)` | 是 | `emailAddress` | `string` | 联系人邮箱 |
| `phone` | `VARCHAR(64)` | 否 | `phone` | `string` | 联系电话 |
| `company` | `VARCHAR(128)` | 否 | `company` | `string` | 公司名称 |
| `department` | `VARCHAR(128)` | 否 | `department` | `string` | 部门名称 |
| `remark` | `VARCHAR(512)` | 否 | `remark` | `string` | 备注 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

> 约束：同一用户的 `user_id` + `email_address` 组合唯一。

**列表响应示例（GET /api/contacts）：**

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "records": [
      {
        "id": 101,
        "name": "Alice Wang",
        "emailAddress": "alice@example.com",
        "phone": "13800138000",
        "company": "Example Corp",
        "department": "Engineering",
        "remark": "项目对接人",
        "createdAt": "2026-02-10T14:00:00+08:00",
        "updatedAt": "2026-05-01T09:00:00+08:00"
      }
    ],
    "page": 1,
    "size": 20,
    "total": 35
  }
}
```

**新增/更新请求示例（POST/PUT /api/contacts）：**

```json
{
  "name": "Alice Wang",
  "emailAddress": "alice@example.com",
  "phone": "13800138000",
  "company": "Example Corp",
  "department": "Engineering",
  "remark": "项目对接人"
}
```

**校验规则：**
- `name`：必填，长度 1-128
- `emailAddress`：必填，合法邮箱格式

**Redis 缓存：** 联系人采用直接读取数据库或独立的短过期时间缓存，不在主缓存设计范围内。

---

### 3.10 login_audit — 登录审计表

**关联 API：** 无。该表仅供后端内部使用，不暴露任何 API 端点。

**字段参考（仅供后端开发）：**

| DB 列 | DB 类型 | 说明 |
|-------|---------|------|
| `id` | `BIGINT` | 主键 |
| `user_id` | `BIGINT` | 用户 ID（失败时可为 NULL） |
| `username` | `VARCHAR(64)` | 尝试登录的用户名 |
| `ip_address` | `VARCHAR(64)` | 客户端 IP |
| `user_agent` | `VARCHAR(512)` | 客户端 User-Agent |
| `success` | `TINYINT(1)` | 1=成功，0=失败 |
| `reason` | `VARCHAR(255)` | 失败原因 |
| `created_at` | `DATETIME(3)` | 操作时间 |

---

### 3.11 mail_intelligence_result — 智能分析结果表

**关联 API：** `/api/intelligence/*` 接口（规划中）。分析结果通过邮件详情接口的扩展字段暴露。

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | — | — | 不暴露 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `message_id` | `BIGINT` | 是 | `messageId` | `number` | 关联邮件 ID |
| `spam_label` | `VARCHAR(32)` | 是 | `spamLabel` | `string` | 垃圾标签：normal/spam/unknown |
| `spam_score` | `DECIMAL(5,4)` | 是 | `spamScore` | `number` | 垃圾评分（0-1） |
| `priority_label` | `VARCHAR(32)` | 是 | `priorityLabel` | `string` | 优先级标签：low/normal/high |
| `priority_score` | `DECIMAL(5,4)` | 是 | `priorityScore` | `number` | 优先级评分（0-1） |
| `risk_level` | `VARCHAR(32)` | 是 | `riskLevel` | `string` | 风险等级：none/low/medium/high/critical |
| `risk_score` | `DECIMAL(5,4)` | 是 | `riskScore` | `number` | 风险评分（0-1） |
| `action_json` | `JSON` | 否 | `actions` | `object` | 建议操作（JSON 对象） |
| `reason_json` | `JSON` | 否 | `reasons` | `object` | 分析依据（JSON 对象） |
| `plugin_name` | `VARCHAR(128)` | 是 | `pluginName` | `string` | 分析插件名称 |
| `plugin_version` | `VARCHAR(64)` | 是 | `pluginVersion` | `string` | 插件版本号 |
| `status` | `VARCHAR(32)` | 是 | `status` | `string` | success/failed/timeout/skipped |
| `error_message` | `VARCHAR(512)` | 否 | `errorMessage` | `string` | 失败原因（仅 status≠success 时） |
| `analyzed_at` | `DATETIME(3)` | 是 | `analyzedAt` | `string` | 分析完成时间 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

> 约束：每个 `message_id` 唯一（`uk_intelligence_message`），即每封邮件最多有一条分析结果。

---

### 3.12 mail_threat_indicator — 威胁指标记录表

**关联 API：** 无独立端点。威胁指标内嵌在智能分析结果中返回。

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | — | — | 不暴露 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `message_id` | `BIGINT` | 是 | — | — | 从分析上下文获取 |
| `intelligence_result_id` | `BIGINT` | 是 | — | — | 关联分析结果 |
| `type` | `VARCHAR(32)` | 是 | `type` | `string` | 指标类型（url/domain/ip/hash/keyword） |
| `value` | `VARCHAR(1024)` | 是 | `value` | `string` | 命中具体值 |
| `risk_level` | `VARCHAR(32)` | 是 | `riskLevel` | `string` | 风险等级 |
| `reason` | `VARCHAR(512)` | 否 | `reason` | `string` | 命中原因说明 |
| `rule_id` | `VARCHAR(128)` | 否 | `ruleId` | `string` | 命中规则 ID |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 命中时间 |

---

### 3.13 mail_push_event — 高优先级推送记录表

**关联 API：** `/api/push-events/*` 接口（规划中）。

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 事件主键 |
| `user_id` | `BIGINT` | 是 | — | — | 从认证上下文获取 |
| `message_id` | `BIGINT` | 是 | `messageId` | `number` | 关联邮件 ID |
| `event_type` | `VARCHAR(64)` | 是 | `eventType` | `string` | 事件类型 |
| `title` | `VARCHAR(255)` | 是 | `title` | `string` | 推送标题 |
| `content` | `VARCHAR(512)` | 否 | `content` | `string` | 推送内容摘要 |
| `priority` | `VARCHAR(32)` | 是 | `priority` | `string` | normal/high/urgent |
| `read_flag` | `TINYINT(1)` | 是 | `readFlag` | `boolean` | 已读标记 |
| `pushed_at` | `DATETIME(3)` | 否 | `pushedAt` | `string` | 推送时间 |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 创建时间 |

**列表查询参数（GET /api/push-events）：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `read` | `boolean` | 否 | 按已读/未读筛选 |
| `priority` | `string` | 否 | 按优先级筛选 |
| `page` | `number` | 否 | 页码，从 1 开始 |
| `size` | `number` | 否 | 每页条数，默认 20 |

---

### 3.14 intelligence_plugin — 智能插件注册表

**关联 API：** `/api/intelligence/plugins/*` 接口（规划中）。

**字段映射表：**

| DB 列 | DB 类型 | 必填 | API 字段 | JSON 类型 | 说明 |
|-------|---------|------|---------|----------|------|
| `id` | `BIGINT` | 是 | `id` | `number` | 插件主键 |
| `name` | `VARCHAR(128)` | 是 | `name` | `string` | 插件名称 |
| `version` | `VARCHAR(64)` | 是 | `version` | `string` | 插件版本 |
| `runtime` | `VARCHAR(32)` | 是 | `runtime` | `string` | 运行环境（python-native 等） |
| `artifact_path` | `VARCHAR(512)` | 是 | — | — | 制品路径（后端内部使用） |
| `checksum` | `VARCHAR(128)` | 否 | — | — | 制品校验和（后端内部使用） |
| `enabled` | `TINYINT(1)` | 是 | `enabled` | `boolean` | 启用状态 |
| `timeout_ms` | `INT` | 是 | `timeoutMs` | `number` | 分析超时（毫秒） |
| `created_at` | `DATETIME(3)` | 是 | `createdAt` | `string` | 注册时间 |
| `updated_at` | `DATETIME(3)` | 是 | `updatedAt` | `string` | 更新时间 |

> 约束：`name` + `version` 组合唯一（`uk_plugin_name_version`）。

---

## 4. 枚举值对照表

### 4.1 用户状态 — `sys_user.status`

| DB 值 | 含义 | API 值 | 说明 |
|-------|------|--------|------|
| `1` | 启用 | `1` | 正常使用 |
| `0` | 禁用 | `0` | 禁止登录 |

### 4.2 文件夹类型 — `mail_folder.type`

| DB/API 值 | 中文名称 | 说明 |
|-----------|---------|------|
| `inbox` | 收件箱 | 默认接收文件夹 |
| `sent` | 已发送 | 已发送邮件 |
| `draft` | 草稿箱 | 未发送草稿 |
| `trash` | 回收站 | 已删除邮件 |
| `spam` | 垃圾邮件 | 垃圾/广告邮件 |
| `custom` | 自定义 | 用户自建文件夹 |

### 4.3 收件人类型 — `mail_recipient.type`

| DB/API 值 | 中文名称 | 说明 |
|-----------|---------|------|
| `to` | 收件人 | 主要收件人 |
| `cc` | 抄送 | 抄送 |
| `bcc` | 密送 | 密送（对其他收件人不可见） |

### 4.4 存储方式 — `mail_attachment.storage_type`

| DB 值 | 含义 | 说明 |
|-------|------|------|
| `local` | 本地文件系统 | 开发环境默认 |
| `minio` | MinIO 对象存储 | 生产环境推荐 |

> 该字段后端内部使用，前端无需关心。

### 4.5 邮件标志位 — `mail_message.*_flag`

所有 `TINYINT(1)` 标志位在 API 中统一使用 `boolean` 类型：

| DB 列 | DB 值 | API 字段 | API 值（JSON） |
|-------|-------|---------|---------------|
| `read_flag` | `0` / `1` | `readFlag` | `false` / `true` |
| `star_flag` | `0` / `1` | `starFlag` | `false` / `true` |
| `draft_flag` | `0` / `1` | `draftFlag` | `false` / `true` |
| `deleted_flag` | `0` / `1` | `deletedFlag` | `false` / `true` |
| `deleted`（软删除） | `0` / `1` | — | 不暴露 |

### 4.6 内容类型 — `mail_message.content_type`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `text` | 纯文本 | `text/plain` |
| `html` | HTML 富文本 | `text/html`，默认值 |

### 4.7 垃圾邮件标签 — `mail_intelligence_result.spam_label`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `normal` | 正常邮件 | 非垃圾邮件 |
| `spam` | 垃圾邮件 | 广告/推广/欺诈 |
| `unknown` | 未判定 | 分析未完成或置信度不足 |

### 4.8 优先级标签 — `mail_intelligence_result.priority_label`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `low` | 低优先级 | 可稍后处理 |
| `normal` | 普通优先级 | 常规处理 |
| `high` | 高优先级 | 需及时关注 |

### 4.9 风险等级 — `mail_intelligence_result.risk_level` / `mail_threat_indicator.risk_level`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `none` | 无风险 | 安全邮件 |
| `low` | 低风险 | 可疑但威胁较低 |
| `medium` | 中风险 | 需人工复核 |
| `high` | 高风险 | 疑似攻击/钓鱼 |
| `critical` | 严重风险 | 确认恶意邮件 |

### 4.10 智能分析状态 — `mail_intelligence_result.status`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `success` | 分析成功 | 插件正常完成分析 |
| `failed` | 分析失败 | 插件执行报错 |
| `timeout` | 分析超时 | 超过插件 timeout_ms |
| `skipped` | 已跳过 | 如邮件过大或格式不支持 |

### 4.11 威胁指标类型 — `mail_threat_indicator.type`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `url` | 恶意 URL | 钓鱼/恶意链接 |
| `domain` | 恶意域名 | 可疑域名/IP 跳转 |
| `ip` | 恶意 IP | C2 服务器等 |
| `hash` | 恶意文件哈希 | 附件/内嵌文件哈希 |
| `keyword` | 高危关键词 | 欺诈/勒索关键词 |

### 4.12 推送优先级 — `mail_push_event.priority`

| DB/API 值 | 含义 | 说明 |
|-----------|------|------|
| `normal` | 普通 | 一般通知 |
| `high` | 高优先级 | 重要事件 |
| `urgent` | 紧急 | 需立即处理 |

---

## 5. 分页查询与数据库查询对应

### 5.1 分页参数转换

| API 参数 | 含义 | SQL 转换 |
|----------|------|---------|
| `page` | 页码（从 1 开始） | `LIMIT (page - 1) * size, size` |
| `size` | 每页条数（默认 20） | 同上 |
| `total` | 总记录数（响应中返回） | `SELECT COUNT(*) FROM ...` |

> 对于 Redis 缓存的邮件列表，分页通过 `ZREVRANGEBYSCORE ... LIMIT offset count` 实现，其中 `offset = (page - 1) * size`，`count = size`。

### 5.2 排序字段映射

| API 排序参数 | DB 列 | 说明 |
|-------------|-------|------|
| `receivedAt`（默认） | `received_at DESC` | 邮件列表按收件时间倒序 |
| `sentAt` | `sent_at DESC` | 按发件时间排序 |
| `createdAt` | `created_at DESC` | 通用按创建时间倒序 |

---

## 6. 软删除约定

所有业务表均包含 `deleted TINYINT(1) NOT NULL DEFAULT 0` 字段，遵循以下约定：

### 6.1 后端查询规则

所有对业务表的查询必须在 WHERE 条件中携带 `AND deleted = 0`。MyBatis-Plus 通过配置自动追加：

```yaml
mybatis-plus:
  global-config:
    db-config:
      logic-delete-field: deleted
      logic-delete-value: 1    # 已删除
      logic-not-delete-value: 0 # 未删除
```

### 6.2 API 行为

| 操作 | API 方法 | 实际 DB 操作 | 说明 |
|------|---------|-------------|------|
| 删除 | `DELETE` | `UPDATE SET deleted = 1` | 软删除，数据可恢复 |
| 查询 | `GET` | `SELECT ... WHERE deleted = 0` | 自动过滤已删除数据 |
| 更新 | `PUT` | `UPDATE ... WHERE deleted = 0` | 不允许更新已删除记录 |

### 6.3 前端行为

- 前端使用 `DELETE` 方法调用删除接口，响应成功即视为删除完成
- 删除后前端应直接从列表中移除该项（乐观更新）或重新拉取列表
- 无需处理 `deleted` 字段，该字段不暴露给前端

---

## 7. Redis 缓存字段对照

本节明确 08-redis-cache-design.md 中各缓存 JSON 字段与数据库列的对应关系。

### 7.1 邮件列表缓存 — 有序集合 Member JSON

**Redis 键：** `mail:message:list:{user_id}:{folder_id}`

| 缓存 JSON 字段 | 对应 DB 列 | 来源表 | 说明 |
|---------------|-----------|--------|------|
| `id` | `id` | `mail_message` | 邮件主键 |
| `subject` | `subject` | `mail_message` | 邮件主题 |
| `from_address` | `from_address` | `mail_message` | 发件人邮箱 |
| `from_name` | `from_name` | `mail_message` | 发件人名称 |
| `read_flag` | `read_flag` | `mail_message` | 已读标记 |
| `star_flag` | `star_flag` | `mail_message` | 星标标记 |
| `attachment_count` | `attachment_count` | `mail_message` | 附件数量 |
| `received_at` | `received_at` | `mail_message` | 收件时间（同时作为 Score） |

### 7.2 邮件详情缓存 — 字符串 JSON

**Redis 键：** `mail:message:detail:{message_id}`

| 缓存 JSON 字段 | 对应 DB 列 | 来源表 |
|---------------|-----------|--------|
| `id` | `id` | `mail_message` |
| `from_address` | `from_address` | `mail_message` |
| `from_name` | `from_name` | `mail_message` |
| `subject` | `subject` | `mail_message` |
| `content` | `content` | `mail_message` |
| `content_type` | `content_type` | `mail_message` |
| `sent_at` | `sent_at` | `mail_message` |
| `received_at` | `received_at` | `mail_message` |
| `read_flag` | `read_flag` | `mail_message` |
| `star_flag` | `star_flag` | `mail_message` |
| `attachments[].id` | `id` | `mail_attachment` |
| `attachments[].original_name` | `original_name` | `mail_attachment` |
| `attachments[].size_bytes` | `size_bytes` | `mail_attachment` |
| `attachments[].content_type` | `content_type` | `mail_attachment` |
| `recipients[].type` | `type` | `mail_recipient` |
| `recipients[].email_address` | `email_address` | `mail_recipient` |
| `recipients[].display_name` | `display_name` | `mail_recipient` |

### 7.3 文件夹统计缓存 — 哈希 Field JSON

**Redis 键：** `mail:folder:stats:{user_id}`

| 缓存 JSON 字段 | 对应 DB 列 | 来源表 |
|---------------|-----------|--------|
| `total_count` | `total_count` | `mail_folder` |
| `unread_count` | `unread_count` | `mail_folder` |
| `name` | `name` | `mail_folder` |
| `type` | `type` | `mail_folder` |

### 7.4 未读计数缓存 — 哈希

**Redis 键：** `mail:unread:counts:{user_id}`

| 缓存字段 | 对应 DB 列 | 来源表 |
|---------|-----------|--------|
| `{folder_id}` → 未读数 | `unread_count` | `mail_folder` |

### 7.5 缓存失效时 DB 回源策略

```
1. 缓存 MISS → 查询 DB → 回填缓存 → 返回数据
2. 写操作 → 先更新 DB → 再删除/失效对应缓存键
3. 文件夹同步 → 全量失效该用户的文件夹统计 + 邮件列表 + 未读计数
4. 登录 → 触发缓存预热（见 08-redis-cache-design.md 第 10 节）
```
