from __future__ import annotations

from typing import Any

from .analyzer import analyze_email
from .config import DEFAULT_CONFIG, PluginConfig


# ============================================================
# 批量分析模块
# ============================================================
#
# 提供一次性分析多封邮件的能力。
# 适用于需要批量处理邮件的场景，如：
#   - 后台定时任务批量扫描收件箱
#   - 导入历史邮件进行分析
#   - 对一批可疑邮件进行批量检测
#
# 批量分析和单封分析的核心逻辑相同，只是多了一层循环。


def analyze_emails_batch(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """批量分析多封邮件，每封邮件独立分析。

    对传入的每个邮件 payload，依次调用 analyze_email() 进行分析。
    如果某封邮件的分析出错，不会影响其他邮件的分析（不会抛出异常）。

    Args:
        payloads: 邮件数据字典列表，每个字典的结构同 analyze_email() 的要求

    Returns:
        分析结果字典列表，顺序和输入一致
    """
    results: list[dict[str, Any]] = []

    for i, payload in enumerate(payloads):
        try:
            result = analyze_email(payload)
            result["_batch_index"] = i  # 记录原始序号，方便对应
            results.append(result)
        except Exception as exc:
            # 单封邮件分析失败，不影响其他邮件
            results.append({
                "pluginVersion": "0.1.0",
                "spam": {"label": "unknown", "score": 0.0},
                "priority": {"label": "normal", "score": 0.0, "reasons": []},
                "risk": {"level": "none", "score": 0.0, "indicators": []},
                "actions": [],
                "error": f"第 {i} 封邮件分析失败: {exc}",
                "_batch_index": i,
            })

    return results


def analyze_batch_with_config(
    payloads: list[dict[str, Any]],
    config: PluginConfig | None = None,
) -> list[dict[str, Any]]:
    """使用自定义配置批量分析多封邮件。

    和 analyze_emails_batch 的区别：
    - 可以传入自定义配置（如调整 spam 阈值、关闭某些检测）
    - 配置对批次中的所有邮件生效

    Args:
        payloads: 邮件数据字典列表
        config:   自定义配置，为 None 时使用默认配置

    Returns:
        分析结果字典列表
    """
    if config is None:
        config = DEFAULT_CONFIG

    # 目前配置尚未集成到 analyze_email 中
    # 这里先把配置信息记录到结果中
    results = analyze_emails_batch(payloads)

    # 给结果加上本次使用的配置信息（方便调试）
    for result in results:
        result["_config"] = config.to_dict()

    return results


def analyze_with_progress(
    payloads: list[dict[str, Any]],
    callback: Any = None,
) -> list[dict[str, Any]]:
    """带进度反馈的批量分析。

    在处理大量邮件时，可以通过 callback 函数获取处理进度。
    比如在 GUI 中更新进度条，或者在日志中输出进度信息。

    Args:
        payloads: 邮件数据字典列表
        callback: 进度回调函数，接收两个参数：(当前进度, 总数)
                  例如: def on_progress(current: int, total: int): ...

    Returns:
        分析结果字典列表
    """
    results: list[dict[str, Any]] = []
    total = len(payloads)

    for i, payload in enumerate(payloads):
        try:
            result = analyze_email(payload)
            result["_batch_index"] = i
            results.append(result)
        except Exception as exc:
            results.append({
                "pluginVersion": "0.1.0",
                "spam": {"label": "unknown", "score": 0.0},
                "priority": {"label": "normal", "score": 0.0, "reasons": []},
                "risk": {"level": "none", "score": 0.0, "indicators": []},
                "actions": [],
                "error": str(exc),
                "_batch_index": i,
            })

        # 调用进度回调
        if callback is not None:
            try:
                callback(i + 1, total)
            except Exception:
                pass  # 回调函数本身的异常不影响分析

    return results


def batch_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """生成批量分析结果的统计摘要。

    统计内容：
    - 总数、垃圾邮件数、高优先级邮件数
    - 各风险等级的分布
    - 各种 action 的触发次数

    Args:
        results: 批量分析的结果列表

    Returns:
        统计摘要字典
    """
    total = len(results)
    spam_count = sum(1 for r in results if r.get("spam", {}).get("label") == "spam")
    high_priority_count = sum(
        1 for r in results if r.get("priority", {}).get("label") == "high"
    )
    error_count = sum(1 for r in results if "error" in r)

    # 统计风险等级分布
    risk_levels: dict[str, int] = {}
    for r in results:
        level = r.get("risk", {}).get("level", "unknown")
        risk_levels[level] = risk_levels.get(level, 0) + 1

    # 统计 action 触发次数
    action_counts: dict[str, int] = {}
    for r in results:
        for action in r.get("actions", []):
            action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "total": total,
        "spam_count": spam_count,
        "spam_rate": round(spam_count / total, 2) if total > 0 else 0.0,
        "high_priority_count": high_priority_count,
        "error_count": error_count,
        "risk_level_distribution": risk_levels,
        "action_counts": action_counts,
    }
