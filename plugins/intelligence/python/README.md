# Python Intelligence Plugin

该目录用于实现智能邮件分析插件，核心能力包括垃圾邮件识别、高优先级识别和恶意内容检测。

## 目录

```text
src/       插件源码
models/    模型文件、规则词典、域名信誉库
tests/     单元测试和样本回归测试
```

## 插件入口

Python 代码最终需要打包为 native 动态库，并导出：

```c
const char* analyze_email_json(const char* request_json);
```

开发阶段可以先使用 CLI 或 HTTP runner 模拟同样的 JSON 输入输出，稳定后再打包成 `.dll`、`.so` 或 `.dylib`。

## 初版检测项

- 垃圾邮件：营销词、中奖词、批量群发特征、异常发件人。
- 高优先邮件：紧急、账单、审批、故障、客户投诉、合同到期。
- 恶意链接：短链接、IP URL、可疑域名、登录仿冒、支付诱导。
- 可疑附件：可执行文件、双后缀、压缩包内脚本。

