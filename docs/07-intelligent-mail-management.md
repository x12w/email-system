# 智能邮件管理模块设计

## 目标

智能邮件管理模块用于在邮件入库后自动完成：

- 垃圾邮件识别。
- 高优先级邮件识别。
- 高危内容检测，例如恶意链接、钓鱼域名、可疑附件、欺骗性发件人。
- 根据分析结果更新邮件标签、风险等级，并触发站内或外部推送。

## 技术边界

| 层 | 技术 | 职责 |
| --- | --- | --- |
| Java 后端 | Spring Boot、MyBatis-Plus、Redis | 分析任务调度、插件调用、结果入库、推送编排 |
| Python 插件 | Python、scikit-learn/onnxruntime/规则引擎可选 | 邮件内容特征提取、分类、风险检测 |
| Native 插件 | `.dll` / `.so` / `.dylib` | Python 分析能力打包后的动态库产物 |
| Redis | Stream 或 List | 异步分析队列、推送事件缓冲 |
| MySQL | 结果表、插件表 | 持久化分析结果、风险项、插件版本 |

## 推荐调用链

```text
IMAP 同步/发信入库
  -> mail_message 保存
  -> 写入 intelligence analyze 任务
  -> Java IntelligenceService 消费任务
  -> PluginManager 加载 native 插件
  -> Python 插件返回 JSON 分析结果
  -> 保存 mail_intelligence_result / mail_threat_indicator
  -> 更新 mail_message 风险和优先级派生字段
  -> 高优先或高危内容写入 mail_push_event
  -> 推送模块发送通知
```

## 插件 ABI 约定

动态库需要导出一个稳定函数，Java 后端通过 JNA/JNI 调用：

```c
const char* analyze_email_json(const char* request_json);
```

请求 JSON：

```json
{
  "requestId": "uuid",
  "messageId": 10001,
  "from": "sender@example.com",
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

响应 JSON：

```json
{
  "pluginVersion": "0.1.0",
  "spam": {
    "label": "normal",
    "score": 0.12
  },
  "priority": {
    "label": "high",
    "score": 0.91,
    "reasons": ["contains urgent payment deadline"]
  },
  "risk": {
    "level": "medium",
    "score": 0.67,
    "indicators": [
      {
        "type": "url",
        "value": "https://example.com/pay",
        "riskLevel": "medium",
        "reason": "new domain and payment keyword"
      }
    ]
  },
  "actions": ["mark_high_priority", "push_notification"]
}
```

## 标签和风险等级

垃圾邮件标签：

| 值 | 说明 |
| --- | --- |
| `normal` | 正常邮件 |
| `spam` | 垃圾邮件 |
| `unknown` | 无法判断 |

优先级标签：

| 值 | 说明 |
| --- | --- |
| `low` | 低优先级 |
| `normal` | 普通 |
| `high` | 高优先级 |

风险等级：

| 值 | 说明 |
| --- | --- |
| `none` | 未发现风险 |
| `low` | 低风险 |
| `medium` | 中风险 |
| `high` | 高风险 |
| `critical` | 严重风险 |

## Python 插件实现建议

初版不建议直接上复杂模型，先采用规则和轻量模型组合：

1. 规则检测：URL 黑名单、短链接、IP 地址链接、危险顶级域名、可执行附件、发件人域名伪装。
2. 文本特征：紧急词、支付词、账号密码词、验证码词、中奖词、威胁词。
3. 统计模型：朴素贝叶斯、逻辑回归或 ONNX 模型。
4. 输出必须包含分数、标签、原因，便于前端解释和人工复核。

## 插件运行要求

- 插件调用必须设置超时，建议 2 秒。
- 插件异常时不阻断邮件入库，结果标记为 `unknown`。
- 插件版本必须入库，方便回溯模型变更导致的分类差异。
- 高危检测要保留命中的 URL、附件名或规则 ID。
- 插件产物按操作系统区分：`plugins/intelligence/native/linux/`、`windows/`、`darwin/`。

## 推送策略

| 条件 | 动作 |
| --- | --- |
| `priority=high` 且 `spam!=spam` | 站内提醒 |
| `riskLevel=high` 或 `critical` | 站内提醒、邮件列表高亮、禁止自动打开链接 |
| `spam=spam` | 移入垃圾邮件或打垃圾标签 |
| 插件失败 | 不推送，只记录异常和待重试状态 |

## 分支建议

智能邮件管理建议拆分为三个分支并行开发：

| 分支 | 职责 |
| --- | --- |
| `feature/intelligence-java-plugin-host` | Java 插件加载、任务消费、结果入库 |
| `feature/intelligence-python-plugin` | Python 分类和风险检测插件 |
| `feature/intelligence-ui-badges` | 前端风险标识、高优先级筛选、推送展示 |

