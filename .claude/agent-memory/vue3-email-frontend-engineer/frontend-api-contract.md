---
name: frontend-api-contract
description: 前后端接口契约：全局规范、错误码、所有接口清单（含请求/响应格式），以 docs/ 目录文档为权威来源
metadata:
  type: reference
---

> **权威来源**：`docs/03-frontend-backend-contract.md` 和 `docs/07-Email-Backend-API.md`。如有冲突，以 `docs/` 目录下的最新文档为准。

## 全局规范

- **API 前缀**：`/api`
- **请求体**：`application/json; charset=utf-8`
- **认证**：`Authorization: Bearer <accessToken>`
- **时间格式**：ISO 8601，例如 `2026-05-17T22:30:00+08:00`
- **分页**：`page` 从 1 开始，`size` 默认 20
- **响应格式**：`{ code: string, message: string, data: any }`，`code="0"` 表示成功

## 统一响应格式

成功：
```json
{ "code": "0", "message": "ok", "data": {} }
```

失败：
```json
{ "code": "AUTH_401", "message": "登录已过期", "data": null }
```

分页：
```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "records": [],
    "page": 1,
    "size": 20,
    "total": 100
  }
}
```

## 错误码

| 错误码 | 说明 | 前端处理 |
|--------|------|----------|
| `0` | 成功 | 正常返回 data |
| `AUTH_401` | 未登录或 token 过期 | 清理状态，跳转 `/login` |
| `AUTH_403` | 无权限 | `ElMessage.error` 提示 |
| `VALIDATION_400` | 参数校验失败 | `ElMessage.error` 提示具体信息 |
| `MAIL_400` | 邮件业务异常 | `ElMessage.error` 提示 |
| `STORAGE_500` | 文件存储异常 | `ElMessage.error` 提示 |
| `SYSTEM_500` | 系统异常 | `ElMessage.error` 提示 |

## 所有接口清单

### 1. 认证模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| POST | `/api/auth/login` | 用户登录 | `api/auth.ts → login()` |
| POST | `/api/auth/logout` | 退出登录 | `api/auth.ts → logout()` |
| POST | `/api/auth/refresh` | 刷新 token | `api/auth.ts → refreshToken()` |
| GET | `/api/auth/me` | 当前用户信息 | `api/auth.ts → getCurrentUser()` |

**登录请求**：
```json
{ "username": "admin", "password": "password" }
```

**登录响应**（前端收到的 data）：
```json
{
  "accessToken": "jwt-token",
  "refreshToken": "refresh-token",
  "expiresIn": 7200,
  "user": { "id": 1, "username": "admin", "displayName": "Admin" }
}
```

### 2. 邮箱账号模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| GET | `/api/mail-accounts` | 邮箱账号列表 | `api/mail.ts → getMailAccounts()` |
| POST | `/api/mail-accounts` | 新增邮箱账号 | `api/mail.ts → createMailAccount()` |
| PUT | `/api/mail-accounts/{id}` | 更新邮箱账号 | `api/mail.ts → updateMailAccount()` |
| DELETE | `/api/mail-accounts/{id}` | 删除邮箱账号 | `api/mail.ts → deleteMailAccount()` |
| POST | `/api/mail-accounts/{id}/test` | 测试 SMTP/IMAP 配置 | `api/mail.ts → testMailAccount()` |

### 3. 文件夹模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| GET | `/api/folders` | 文件夹列表和未读数 | `api/folder.ts → getFolderList()` |
| POST | `/api/folders/sync` | 同步远程文件夹 | `api/folder.ts → syncFolders()` |

### 4. 邮件核心模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| GET | `/api/messages` | 邮件列表（支持 spamLabel/priorityLabel/riskLevel 筛选） | `api/mail.ts → getMailList()` |
| GET | `/api/messages/{id}` | 邮件详情 | `api/mail.ts → getMailDetail()` |
| POST | `/api/messages/send` | 发送邮件 | `api/mail.ts → sendMail()` |
| POST | `/api/messages/drafts` | 保存草稿 | `api/mail.ts → saveDraft()` |
| PUT | `/api/messages/{id}/read` | 标记已读/未读 | `api/mail.ts → markAsRead()` / `markAsUnread()` |
| DELETE | `/api/messages/{id}` | 删除邮件（软删除） | `api/mail.ts → deleteMail()` |

**新增接口（来自 docs/07-Email-Backend-API.md，待对接 ❌）**：

| 方法 | 路径 | 说明 | 前端调用（待实现） |
|------|------|------|--------------------|
| POST | `/api/messages/process` | 接收并处理新邮件（触发 AI 拦截） | `api/mail.ts → processMessage()` |

**邮件列表查询参数**：
```
GET /api/messages?accountId=1&folderId=1&keyword=invoice&read=0&spamLabel=normal&priorityLabel=high&riskLevel=high&page=1&size=20
```

**发送邮件请求**：
```json
{
  "accountId": 1,
  "to": ["user@example.com"],
  "cc": [],
  "bcc": [],
  "subject": "Hello",
  "contentType": "html",
  "content": "<p>Hello</p>",
  "attachmentIds": [1, 2]
}
```

**process 请求**（来自 docs/07）：
```json
{
  "userId": 1,
  "accountId": 101,
  "messageUid": "UID-2026-XYZ",
  "fromAddress": "sender@example.com",
  "to": ["receiver@example.com"],
  "cc": [],
  "bcc": [],
  "subject": "关于项目进度的汇报",
  "content": "邮件正文详细内容..."
}
```

### 5. 附件模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| POST | `/api/attachments` | 上传附件 | `api/mail.ts → uploadAttachment()` |
| GET | `/api/attachments/{id}/download` | 下载附件 | `api/mail.ts → downloadAttachment()` |
| DELETE | `/api/attachments/{id}` | 删除未发送附件 | `api/mail.ts → deleteAttachment()` |

### 6. 联系人模块（已对接 ✅）

| 方法 | 路径 | 说明 | 前端调用 |
|------|------|------|----------|
| GET | `/api/contacts` | 联系人列表 | `api/contact.ts → getContactList()` |
| POST | `/api/contacts` | 新增联系人 | `api/contact.ts → createContact()` |
| PUT | `/api/contacts/{id}` | 更新联系人 | `api/contact.ts → updateContact()` |
| DELETE | `/api/contacts/{id}` | 删除联系人 | `api/contact.ts → deleteContact()` |

### 7. AI 智能分析模块（待实现 ❌）

| 方法 | 路径 | 说明 | 前端调用（待实现） |
|------|------|------|--------------------|
| GET | `/api/intelligence/messages/{messageId}` | 获取邮件 AI 分析结果 | `api/intelligence.ts → getMessageAnalysis()` |

**成功响应（分析完成）**：
```json
{
  "messageId": 1789234567,
  "spamLabel": "normal",
  "spamScore": 0.12,
  "priorityLabel": "high",
  "priorityScore": 0.91,
  "riskLevel": "medium",
  "riskScore": 0.67,
  "pluginName": "python-mail-intelligence",
  "pluginVersion": "0.1.0",
  "analyzedAt": "2026-05-27T15:30:05+08:00",
  "threats": [
    {
      "type": "url",
      "value": "https://example.com/pay",
      "riskLevel": "medium",
      "reason": "new domain and payment keyword"
    }
  ]
}
```

**降级返回（分析未完成）**：
```json
{
  "messageId": 1789234567,
  "spamLabel": "processing",
  "analyzedAt": null,
  "threats": []
}
```

> 注：`code="0"`, `message="AI 分析任务正在排队或处理中，请稍后刷新"`

## 前端 Axios 拦截器处理规则

已在 `@/utils/request.ts` 中实现：

1. **请求拦截器**：自动从 localStorage 注入 `Authorization: Bearer <token>`
2. **响应拦截器（成功）**：`code !== '0'` → reject；`code === 'AUTH_401'` → 清理 + 跳转；正常 → 返回 `body.data`
3. **响应拦截器（错误）**：HTTP 401 → 清理 + 跳转
4. **文件上传**：`multipart/form-data`，字段名 `file`
