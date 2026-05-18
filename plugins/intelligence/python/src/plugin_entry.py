from __future__ import annotations

import json

# 注意这里的导入方式：from .analyzer import analyze_email
# 开头的点号 . 表示"相对导入"，意思是"从当前包（src 目录）中的 analyzer 模块导入"
# 因为 src 目录下有 __init__.py，它已经是一个 Python 包了
# 所以要用相对导入而不是直接 from analyzer import ...
from .analyzer import analyze_email


def analyze_email_json(request_json: str) -> str:
    """从外部接收 JSON 格式的请求，分析邮件并返回 JSON 格式的结果。

    这个函数是该插件的外部接口（entry point）。
    外部程序（可能是其他语言写的，比如 C++ 或 Go）调用这个函数时，
    传入和返回的都是 JSON 字符串，不涉及 Python 对象。

    这样做的好处：
    - 语言无关：外部程序不需要了解 Python 内部的数据结构
    - 便于调试：JSON 是纯文本，可以直接查看和记录日志
    - 松耦合：外部和内部通过 JSON 协议通信，互不依赖实现细节

    工作流程：
    1. 接收 JSON 字符串（request_json）
    2. 用 json.loads 把 JSON 解析成 Python 字典
    3. 调用 analyze_email() 核心分析函数
    4. 用 json.dumps 把分析结果字典转回 JSON 字符串
    5. 返回 JSON 字符串给调用方

    异常处理：
    如果过程中出现任何异常（比如 JSON 格式不对、字段缺失等），
    不会崩溃，而是返回一个"安全"的默认结果，同时在结果中包含错误信息。
    这种"永不崩溃"的设计对插件系统非常重要——一个插件的崩溃
    不应该影响整个邮件系统的运行。

    Args:
        request_json: JSON 格式的请求字符串，包含邮件的各种字段

    Returns:
        JSON 格式的分析结果字符串
    """
    try:
        # json.loads：把 JSON 字符串解析成 Python 字典
        # 例如输入 '{"subject": "Hello", "plainText": "..."}'
        # 会变成 Python 字典 {"subject": "Hello", "plainText": "..."}
        payload = json.loads(request_json)

        # 调用核心分析函数
        result = analyze_email(payload)

        # json.dumps：把 Python 对象转回 JSON 字符串
        # ensure_ascii=False 表示允许输出中文等非 ASCII 字符
        #（而不是把中文转成 \uXXXX 的转义序列）
        return json.dumps(result, ensure_ascii=False)

    except Exception as exc:
        # 任何异常都不会让程序崩溃，而是返回一个默认的安全结果
        # 风险等级设为 "none"（无风险），避免误报
        # 同时把错误信息包含在返回结果中，方便排查问题
        return json.dumps(
            {
                "pluginVersion": "0.1.0",
                "spam": {"label": "unknown", "score": 0.0},
                "priority": {"label": "normal", "score": 0.0, "reasons": []},
                "risk": {"level": "none", "score": 0.0, "indicators": []},
                "actions": [],
                "error": str(exc),  # 错误信息，方便调试
            },
            ensure_ascii=False,
        )
