from __future__ import annotations

import json
from pathlib import Path

# ============================================================
# 关键词词库加载器
# ============================================================
#
# 关键词数据存放在 data/ 目录下的 JSON 文件中，由本模块加载。
# 这样做的好处：
#   1. 主代码（analyzer.py）不被大量关键词数据撑满，逻辑更清晰
#   2. 修改词库只需要改 JSON 文件，不需要动 Python 代码
#   3. JSON 是纯文本格式，方便用其他工具（爬虫、脚本）生成和更新
#
# 加载时机：模块被 import 时一次性读入内存。
# 这样后续调用分析函数时不用重复读文件，效率更高。

# __file__ 是当前文件（keywords.py）的完整路径。
# 用 Path(__file__).resolve().parent.parent 找到项目根目录，
# 然后拼接 /data/ 得到数据目录路径。
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_keywords(filename: str) -> dict[float, list[str]]:
    """从 data/ 目录下的 JSON 文件加载关键词词库。

    JSON 文件里，键是权重（字符串），值是关键词列表。
    因为 JSON 格式的键必须是字符串，所以加载后要把键转回 float。

    Args:
        filename: JSON 文件名，如 "high_priority_keywords.json"

    Returns:
        字典 {权重(float): [关键词列表]}
    """
    filepath = _DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        raw: dict[str, list[str]] = json.load(f)
    # JSON 只支持字符串作为键名，所以需要把 "1.0" 转成 1.0（float）
    return {float(weight): keywords for weight, keywords in raw.items()}


# ============================================================
# 词库变量
# ============================================================
# 模块加载时自动从 JSON 文件读取，结果就是普通的 dict，用法和之前完全一样。
# 这三个变量加了下划线 _ 前缀，表示"内部使用"（Python 约定）。
# 外部模块（analyzer.py）通过 from .keywords import ... 来引用。

# 高优先级关键词词库
# 来源：大量关于紧急邮件、高优先级邮件的研究和最佳实践。
_HIGH_PRIORITY_KEYWORDS = _load_keywords("high_priority_keywords.json")

# 垃圾邮件关键词词库
# 来源：SpamAssassin 规则、各大邮件服务商公开的垃圾邮件过滤词、
#       营销邮件避坑指南、外贸邮件过滤研究报告等。
_SPAM_KEYWORDS = _load_keywords("spam_keywords.json")

# 钓鱼邮件关键词词库
# 来源：2025 年钓鱼攻击报告、各大安全厂商威胁情报、反钓鱼最佳实践。
_PHISHING_KEYWORDS = _load_keywords("phishing_keywords.json")
