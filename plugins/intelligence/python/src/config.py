from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ============================================================
# 插件配置模块
# ============================================================
#
# 所有的可配置参数都集中在这里，方便统一管理和修改。
# 默认值适用于大多数场景，但可以通过传入字典覆盖。
#
# 用法：
#   config = PluginConfig()                           # 使用默认配置
#   config = PluginConfig.load_from_dict({"spam_threshold": 0.7})  # 自定义
#   print(config.spam_threshold)                       # 读取配置项


@dataclass
class PluginConfig:
    """邮件分析插件的全部配置项。

    所有阈值、开关、参数都定义在这里。每个字段都有默认值，
    所以大多数情况下直接用 PluginConfig() 即可。

    Attributes:
        # ---------- 评分阈值 ----------
        spam_threshold:          判定为垃圾邮件的分数阈值（0.0 ~ 1.0）
        priority_threshold:      判定为高优先级的分数阈值（0.0 ~ 1.0）
        risk_indicator_weight:   每个风险指标对最终风险分的贡献值

        # ---------- 功能开关 ----------
        enable_link_detection:        是否启用链接风险检测
        enable_attachment_detection:  是否启用附件风险检测
        enable_sender_detection:      是否启用发件人伪造检测
        enable_phishing_detection:    是否启用钓鱼文本检测
        enable_html_analysis:         是否启用 HTML 内容分析
        enable_header_analysis:       是否启用邮件头分析
        enable_reputation_check:      是否检查域名/IP 声誉（需要网络请求）

        # ---------- 检测参数 ----------
        max_links_to_check:     最多检测多少个链接（0 表示不限制）
        max_attachments_to_check: 最多检测多少个附件
        homoglyph_sensitivity:   同形字符检测灵敏度（0.0 ~ 1.0，越大越敏感）
        typosquatting_max_edit_distance: 域名抢注检测的最大编辑距离
    """

    # ---------- 评分阈值 ----------
    spam_threshold: float = 0.6
    priority_threshold: float = 0.5
    risk_indicator_weight: float = 0.25

    # ---------- 功能开关 ----------
    enable_link_detection: bool = True
    enable_attachment_detection: bool = True
    enable_sender_detection: bool = True
    enable_phishing_detection: bool = True
    enable_html_analysis: bool = True
    enable_header_analysis: bool = True
    enable_reputation_check: bool = False  # 需要网络请求，默认关闭

    # ---------- 检测参数 ----------
    max_links_to_check: int = 0
    max_attachments_to_check: int = 0
    homoglyph_sensitivity: float = 1.0
    typosquatting_max_edit_distance: int = 2

    @classmethod
    def load_from_dict(cls, data: dict[str, Any]) -> "PluginConfig":
        """从字典加载配置，缺失的字段使用默认值。

        这样可以只传需要覆盖的配置项，不用每次都提供全部参数。

        Args:
            data: 配置字典，键为字段名，值为配置值。
                  例如 {"spam_threshold": 0.7, "enable_html_analysis": False}

        Returns:
            新的 PluginConfig 实例
        """
        # 只提取 PluginConfig 中定义的字段（忽略多余的键）
        valid_keys = set(cls.__dataclass_fields__)  # 所有合法的字段名
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        """把配置转成字典，方便序列化为 JSON。

        Returns:
            字典格式的配置
        """
        return {
            "spam_threshold": self.spam_threshold,
            "priority_threshold": self.priority_threshold,
            "risk_indicator_weight": self.risk_indicator_weight,
            "enable_link_detection": self.enable_link_detection,
            "enable_attachment_detection": self.enable_attachment_detection,
            "enable_sender_detection": self.enable_sender_detection,
            "enable_phishing_detection": self.enable_phishing_detection,
            "enable_html_analysis": self.enable_html_analysis,
            "enable_header_analysis": self.enable_header_analysis,
            "enable_reputation_check": self.enable_reputation_check,
            "max_links_to_check": self.max_links_to_check,
            "max_attachments_to_check": self.max_attachments_to_check,
            "homoglyph_sensitivity": self.homoglyph_sensitivity,
            "typosquatting_max_edit_distance": self.typosquatting_max_edit_distance,
        }


# 全局默认配置实例
# 其他地方可以直接 from .config import DEFAULT_CONFIG 来使用
DEFAULT_CONFIG = PluginConfig()
