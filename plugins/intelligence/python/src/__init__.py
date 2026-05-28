from __future__ import annotations

from .analyzer import analyze_email
from .batch_analyzer import (
    analyze_batch_with_config,
    analyze_emails_batch,
    analyze_with_progress,
    batch_summary,
)
from .config import DEFAULT_CONFIG, PluginConfig
from .html_analyzer import (
    analyze_html_content,
    count_external_images,
    detect_hidden_content,
    detect_tracking_pixels,
    extract_links_from_html,
    extract_text_from_html,
)
from .plugin_entry import analyze_email_json

__all__ = [
    # —— 核心分析 ——
    "analyze_email",         # 单封邮件分析（核心入口）
    "analyze_email_json",    # JSON 接口（给外部程序调用）

    # —— 批量分析 ——
    "analyze_emails_batch",      # 批量分析多封邮件
    "analyze_batch_with_config",  # 自定义配置的批量分析
    "analyze_with_progress",      # 带进度回调的批量分析
    "batch_summary",              # 批量结果统计摘要

    # —— HTML 分析 ——
    "analyze_html_content",     # HTML 综合分析
    "extract_text_from_html",   # 从 HTML 提取纯文本
    "detect_hidden_content",    # 检测隐藏内容
    "detect_tracking_pixels",   # 检测跟踪像素
    "count_external_images",    # 统计外部图片
    "extract_links_from_html",  # 从 HTML 提取链接

    # —— 配置 ——
    "PluginConfig",     # 配置类
    "DEFAULT_CONFIG",   # 默认配置实例
]
