# 智能邮件分析插件 — I/O 契约

## 概述

本文档定义 Python 智能邮件分析插件与 Java 后端之间的 I/O 契约。  
插件通过 C ABI (`const char* analyze_email_json(const char* request_json)`) 被调用，输入输出均为 UTF-8 JSON 字符串。

本契约的 JSON Schema 文件见 [`plugin-contract-schema.json`](plugin-contract-schema.json)。

---

## 输入格式

```json
{
  "requestId": "uuid",
  "messageId": 10001,
  "from": "sender@example.com",
  "fromName": "Sender",
  "to": ["user@example.com"],
  "subject": "Invoice",
  "plainText": "mail body",
  "html": "<p>mail body</p>",
  "links": ["https://example.com/pay"],
  "attachments": [
    {
      "id": 1,
      "filename": "invoice.pdf",
      "contentType": "application/pdf",
      "sizeBytes": 204800
    }
  ],
  "locale": "zh-CN"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `requestId` | string | 否 | 请求追踪 ID，原样回传 |
| `messageId` | integer | 否 | 邮件 ID，原样回传 |
| `from` | string | 否 | 发件人邮箱地址 |
| `fromName` | string | 否 | 发件人显示名称 |
| `to` | string[] | 否 | 收件人地址列表 |
| `subject` | string | 否 | 邮件主题 |
| `plainText` | string | 否 | 纯文本正文 |
| `html` | string | 否 | HTML 正文 |
| `links` | string[] | 否 | 邮件中的链接列表 |
| `attachments` | object[] | 否 | 附件列表，每项含 `id`、`filename` |
| `locale` | string | 否 | 语言区域，如 `zh-CN` |

---

## 输出格式

### 成功响应

```json
{
  "pluginVersion": "0.1.0",
  "analyzedAt": "2026-05-28T10:30:00+00:00",
  "spam": {
    "label": "normal",
    "score": 0.12
  },
  "priority": {
    "label": "high",
    "score": 0.91,
    "reasons": ["邮件包含紧急关键词，建议立即查看"]
  },
  "risk": {
    "level": "medium",
    "score": 0.67,
    "indicators": [
      {
        "type": "url",
        "value": "https://example.com/pay",
        "riskLevel": "medium",
        "reason": "链接中包含敏感操作关键词（登录/密码/支付）"
      }
    ]
  },
  "actions": ["mark_high_priority", "push_notification"]
}
```

### 错误响应

```json
{
  "pluginVersion": "0.1.0",
  "code": "PLUGIN_VALIDATION_400",
  "message": "JSON 解析失败: Expecting value: line 1 column 1 (char 0)",
  "spam": { "label": "unknown", "score": 0.0 },
  "priority": { "label": "normal", "score": 0.0, "reasons": [] },
  "risk": { "level": "none", "score": 0.0, "indicators": [] },
  "actions": []
}
```

---

## 字段说明

### 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `pluginVersion` | string | 是 | 插件版本号，用于结果回溯 |
| `analyzedAt` | string | 否 | ISO 8601 分析时间 |
| `spam` | object | 是 | 垃圾邮件判定结果 |
| `priority` | object | 是 | 优先级判定结果 |
| `risk` | object | 是 | 风险检测结果 |
| `actions` | string[] | 是 | 建议执行的操作 |
| `requestId` | string | 否 | 原样回传的请求 ID |
| `messageId` | integer | 否 | 原样回传的邮件 ID |
| `code` | string | 否 | 错误码，成功时不出现 |
| `message` | string | 否 | 错误描述，成功时不出现 |

### spam

| 字段 | 类型 | 说明 |
|------|------|------|
| `label` | `normal` / `spam` / `unknown` | 垃圾邮件标签 |
| `score` | 0.0 ~ 1.0 | 垃圾邮件分数 |

### priority

| 字段 | 类型 | 说明 |
|------|------|------|
| `label` | `low` / `normal` / `high` | 优先级标签 |
| `score` | 0.0 ~ 1.0 | 优先级分数 |
| `reasons` | string[] | 优先级判断理由 |

### risk

| 字段 | 类型 | 说明 |
|------|------|------|
| `level` | `none` / `low` / `medium` / `high` / `critical` | 综合风险等级 |
| `score` | 0.0 ~ 1.0 | 风险分数 |
| `indicators` | Indicator[] | 风险指标列表 |

### Indicator（风险指标）

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `url` / `attachment` / `sender` / `phishing` / `html` | 风险类型 |
| `value` | string | 触发风险的具体内容 |
| `riskLevel` | `low` / `medium` / `high` | 单条指标风险等级 |
| `reason` | string | 风险原因描述 |

---

## 错误码

| 错误码 | 说明 | 触发场景 |
|--------|------|----------|
| `PLUGIN_VALIDATION_400` | 输入 JSON 格式错误或字段缺失 | `json.JSONDecodeError` |
| `PLUGIN_DNS_TIMEOUT` | DNS 查询超时 | SPF/DKIM/DMARC/DNSBL 查询超时 |
| `PLUGIN_INTERNAL_500` | 插件内部异常 | Python 解释器或未捕获异常 |

---

## 推送策略（源自 docs/07-intelligent-mail-management.md）

| 条件 | 动作 |
|------|------|
| `priority=high` 且 `spam!=spam` | 站内提醒 |
| `risk.level=high` 或 `critical` | 站内提醒、邮件列表高亮、禁止自动打开链接 |
| `spam=spam` | 移入垃圾邮件或打垃圾标签 |
| 插件失败 | 不推送，记录异常和待重试状态 |
