# 后端 API 接口文档

## 1. 全局规范说明

* **统一请求前缀**：`/api`
* **数据传输格式**：`application/json; charset=utf-8`
* **认证方式**：请求头必须携带 `Authorization: Bearer <accessToken>`
* **统一响应体格式**：
    后端所有接口必须返回团队约定的统一 JSON 结构：

```json
{
  "code": "0",       // 状态码：字符串 "0" 表示成功，非 "0" 表示异常
  "message": "ok",   // 提示信息
  "data": {}         // 具体的业务数据，无数据时为 null
}
```

## 2. 邮件核心业务模块

### 2.1 接收并处理新邮件（触发AI拦截）

* **接口功能**：邮件服务器网关投递/前端同步新邮件，后端执行基础校验、重复校验、入库并异步触发智能分析。
* **请求路径**：`POST /api/messages/process`
* **请求方式**：`POST`

#### 请求参数

| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| userId | Long | 是 | 用户唯一ID | 1 |
| accountId | Long | 是 | 绑定的邮箱账号ID | 101 |
| messageUid | String | 是 | 同账号下邮件唯一UID (用于防重) | "UID-2026-XYZ" |
| fromAddress | String | 是 | 发件人邮箱 | sender@example.com |
| to | Array | 是 | 收件人邮箱列表 | ["receiver@example.com"] |
| cc | Array | 否 | 抄送人邮箱列表 | [] |
| bcc | Array | 否 | 密送人邮箱列表 | [] |
| subject | String | 否 | 邮件标题 | 关于项目进度的汇报 |
| content | String | 否 | 邮件正文内容 | 邮件正文详细内容... |

**请求示例：**

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
  "content": "核心大佬您好，本周接口文档已对齐。"
}
```

#### 响应结果

* **成功响应**：

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "mailId": 1789234567,
    "status": "PROCESSING"
  }
}
```

* **参数缺失 (VALIDATION_400)**：

```json
{
  "code": "VALIDATION_400",
  "message": "参数校验失败：userId, accountId, messageUid, fromAddress, to 不能为空",
  "data": null
}
```

* **重复邮件拦截 (MAIL_400)**：

```json
{
  "code": "MAIL_400",
  "message": "该账号下已存在相同UID的邮件，请勿重复投递",
  "data": null
}
```

### 2.2 分页查询邮件列表

* **接口功能**：供前端控制台拉取邮件列表，支持文件夹、智能标签及多条件过滤筛选。
* **请求路径**：`GET /api/messages`
* **请求方式**：`GET`

#### 请求参数（Query参数）

| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| page | Integer | 否 | 当前页码 (从1开始，默认1) | 1 |
| size | Integer | 否 | 每页条数 (默认20) | 20 |
| folderId | Long | 否 | 文件夹ID | 1 |
| keyword | String | 否 | 搜索关键字 | invoice |
| spamLabel | String | 否 | 智能垃圾邮件标签 (normal/spam) | normal |
| priorityLabel | String | 否 | 智能优先级标签 (high/low) | high |
| riskLevel | String | 否 | 智能风险等级 (high/medium/low) | high |

#### 响应结果

* **成功响应**：

```json
{
  "code": "0",
  "message": "ok",
  "data": {
    "records": [
      {
        "id": 1789234567,
        "userId": 1,
        "accountId": 101,
        "subject": "关于项目进度的汇报",
        "fromAddress": "sender@example.com",
        "spamLabel": "normal",
        "priorityLabel": "high",
        "riskLevel": "medium",
        "createTime": "2026-05-27T15:30:00+08:00"
      }
    ],
    "page": 1,
    "size": 20,
    "total": 1
  }
}
```

### 2.3 邮件软删除（逻辑删除）

* **接口功能**：用户点击删除邮件，将邮件标记为删除状态，不物理删除数据。
* **请求路径**：`DELETE /api/messages/{id}`
* **请求方式**：`DELETE`

#### 请求参数（路径参数）

| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| id | Long | 是 | 邮件数据库自增ID | 1789234567 |

#### 响应结果

* **成功响应**：

```json
{
  "code": "0",
  "message": "ok",
  "data": true
}
```

## 3. 智能分析模块

### 3.1 获取指定邮件的智能分析结果

* **接口功能**：前端点击查看某封邮件的详细 AI 分析指标、垃圾概率、风险威胁项。
* **请求路径**：`GET /api/intelligence/messages/{messageId}`
* **请求方式**：`GET`

#### 请求参数（路径参数）

| 参数名 | 类型 | 是否必填 | 说明 | 示例 |
| --- | --- | --- | --- | --- |
| messageId | Long | 是 | 邮件数据库自增ID | 1789234567 |

#### 响应结果

* **成功响应（分析完成）**：

```json
{
  "code": "0",
  "message": "ok",
  "data": {
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
}
```

* **分析尚未结束降级返回**：

```json
{
  "code": "0",
  "message": "AI 分析任务正在排队或处理中，请稍后刷新",
  "data": {
    "messageId": 1789234567,
    "spamLabel": "processing",
    "analyzedAt": null,
    "threats": []
  }
}
```