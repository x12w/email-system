# 前后端对接规范

## 基础约定

- 后端 API 前缀：`/api`
- 请求体：`application/json`
- 响应体：统一 JSON
- 认证方式：`Authorization: Bearer <accessToken>`
- 时间格式：ISO 8601，例如 `2026-05-17T22:30:00+08:00`
- 分页参数：`page` 从 1 开始，`size` 默认 20

## 统一响应

成功：

```json
{
  "code": "0",
  "message": "ok",
  "data": {}
}
```

失败：

```json
{
  "code": "AUTH_401",
  "message": "登录已过期",
  "data": null
}
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

## 错误码建议

| 错误码 | 说明 |
| --- | --- |
| `0` | 成功 |
| `AUTH_401` | 未登录或 token 过期 |
| `AUTH_403` | 无权限 |
| `VALIDATION_400` | 参数校验失败 |
| `MAIL_400` | 邮件业务异常 |
| `INTELLIGENCE_400` | 智能分析请求异常 |
| `INTELLIGENCE_503` | 智能分析插件不可用 |
| `STORAGE_500` | 文件存储异常 |
| `SYSTEM_500` | 系统异常 |

## 初版接口清单

### 认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/auth/login` | 用户登录 |
| `POST` | `/api/auth/logout` | 退出登录 |
| `POST` | `/api/auth/refresh` | 刷新 token |
| `GET` | `/api/auth/me` | 当前用户信息 |

登录请求：

```json
{
  "username": "admin",
  "password": "password"
}
```

登录响应：

```json
{
  "accessToken": "jwt-token",
  "refreshToken": "refresh-token",
  "expiresIn": 7200,
  "user": {
    "id": 1,
    "username": "admin",
    "displayName": "Admin"
  }
}
```

### 邮箱账号

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/mail-accounts` | 邮箱账号列表 |
| `POST` | `/api/mail-accounts` | 新增邮箱账号 |
| `PUT` | `/api/mail-accounts/{id}` | 更新邮箱账号 |
| `DELETE` | `/api/mail-accounts/{id}` | 删除邮箱账号 |
| `POST` | `/api/mail-accounts/{id}/test` | 测试 SMTP/IMAP 配置 |

### 邮件文件夹

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/folders` | 文件夹列表和未读数 |
| `POST` | `/api/folders/sync` | 同步远程文件夹 |

### 邮件

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/messages` | 邮件列表 |
| `GET` | `/api/messages/{id}` | 邮件详情 |
| `POST` | `/api/messages/send` | 发送邮件 |
| `POST` | `/api/messages/drafts` | 保存草稿 |
| `PUT` | `/api/messages/{id}/read` | 标记已读或未读 |
| `DELETE` | `/api/messages/{id}` | 删除邮件 |

邮件列表查询：

```text
GET /api/messages?folderId=1&keyword=invoice&read=false&page=1&size=20
```

发送邮件请求：

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

### 附件

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/attachments` | 上传附件 |
| `GET` | `/api/attachments/{id}/download` | 下载附件 |
| `DELETE` | `/api/attachments/{id}` | 删除未发送附件 |

### 联系人

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/contacts` | 联系人列表 |
| `POST` | `/api/contacts` | 新增联系人 |
| `PUT` | `/api/contacts/{id}` | 更新联系人 |
| `DELETE` | `/api/contacts/{id}` | 删除联系人 |

### 智能邮件管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/intelligence/messages/{messageId}` | 查询单封邮件智能分析结果 |
| `POST` | `/api/intelligence/messages/{messageId}/analyze` | 手动触发邮件智能分析 |
| `GET` | `/api/intelligence/threats` | 查询风险项列表 |
| `GET` | `/api/intelligence/push-events` | 查询高优先或高危推送事件 |
| `PUT` | `/api/intelligence/push-events/{id}/read` | 标记推送事件已读 |
| `GET` | `/api/intelligence/plugins` | 查询智能插件版本和状态 |

邮件智能分析结果响应：

```json
{
  "messageId": 10001,
  "spamLabel": "normal",
  "spamScore": 0.12,
  "priorityLabel": "high",
  "priorityScore": 0.91,
  "riskLevel": "medium",
  "riskScore": 0.67,
  "pluginName": "python-mail-intelligence",
  "pluginVersion": "0.1.0",
  "analyzedAt": "2026-05-17T22:30:00+08:00",
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

邮件列表可扩展筛选参数：

```text
GET /api/messages?folderId=1&spamLabel=normal&priorityLabel=high&riskLevel=high&page=1&size=20
```

## 前端 Axios 约定

1. 请求拦截器统一注入 `Authorization`。
2. 响应拦截器只向页面返回 `data.data`。
3. `AUTH_401` 统一跳转登录页，并清理 Pinia 中的认证状态。
4. 文件上传使用 `multipart/form-data`，字段名为 `file`。
