from __future__ import annotations

import json

from ._version import __version__
from .analyzer import analyze_email


# ============================================================
# 错误码定义
# ============================================================
# 遵循 docs/03-frontend-backend-contract.md 的错误码规范，
# 使用 PLUGIN_ 前缀与后端错误码区分。
# ============================================================

# 成功
SUCCESS = "0"

# 输入错误
ERR_INVALID_JSON = "PLUGIN_VALIDATION_400"      # JSON 格式错误或字段缺失

# DNS 相关
ERR_DNS_TIMEOUT = "PLUGIN_DNS_TIMEOUT"           # DNS 查询超时（如 SPF/DKIM/DMARC）

# 系统内部错误
ERR_INTERNAL = "PLUGIN_INTERNAL_500"             # Python 解释器或内部异常


def _make_error(code: str, message: str) -> str:
    """构造标准错误响应 JSON。

    Args:
        code:    错误码，遵循 PLUGIN_ 前缀约定
        message: 人类可读的错误描述

    Returns:
        JSON 格式的错误响应字符串
    """
    return json.dumps(
        {
            "pluginVersion": __version__,
            "code": code,
            "message": message,
            "spam": {"label": "unknown", "score": 0.0},
            "priority": {"label": "normal", "score": 0.0, "reasons": []},
            "risk": {"level": "none", "score": 0.0, "indicators": []},
            "actions": [],
        },
        ensure_ascii=False,
    )


def analyze_email_json(request_json: str) -> str:
    """从外部接收 JSON 格式的请求，分析邮件并返回 JSON 格式的结果。

    这个函数是该插件的外部接口（entry point）。
    外部程序（可能是其他语言写的，比如 C++ 或 Go）调用这个函数时，
    传入和返回的都是 JSON 字符串，不涉及 Python 对象。

    这样做的好处：
    - 语言无关：外部程序不需要了解 Python 内部的数据结构
    - 便于调试：JSON 是纯文本，可以直接查看和记录日志
    - 松耦合：外部和内部通过 JSON 协议通信，互不依赖实现细节

    错误处理（遵循 07-intelligent-mail-management.md 的要求）：
    - 插件异常时不阻断邮件入库，结果标记为 unknown
    - 所有异常都被捕获，返回标准错误响应
    - 错误码遵循 PLUGIN_ 前缀约定

    Args:
        request_json: JSON 格式的请求字符串，包含邮件的各种字段

    Returns:
        JSON 格式的分析结果字符串
    """
    try:
        payload = json.loads(request_json)
        result = analyze_email(payload)
        result["pluginVersion"] = __version__
        return json.dumps(result, ensure_ascii=False)

    except json.JSONDecodeError as exc:
        return _make_error(
            ERR_INVALID_JSON,
            f"JSON 解析失败: {exc}",
        )
    except Exception as exc:
        return _make_error(
            ERR_INTERNAL,
            f"分析异常: {exc}",
        )
