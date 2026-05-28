from __future__ import annotations

from src.batch_analyzer import (
    analyze_batch_with_config,
    analyze_emails_batch,
    analyze_with_progress,
    batch_summary,
)
from src.config import PluginConfig


class TestAnalyzeEmailsBatch:
    """测试批量分析。"""

    def test_empty_list(self):
        """空列表应返回空结果"""
        assert analyze_emails_batch([]) == []

    def test_single_email(self):
        """单封邮件分析"""
        results = analyze_emails_batch([{"subject": "正常邮件", "plainText": "你好"}])
        assert len(results) == 1
        assert results[0]["_batch_index"] == 0

    def test_multiple_emails(self):
        """多封邮件顺序应保持一致"""
        payloads = [
            {"subject": "A", "plainText": "a"},
            {"subject": "B", "plainText": "b"},
        ]
        results = analyze_emails_batch(payloads)
        assert len(results) == 2
        assert results[0]["_batch_index"] == 0
        assert results[1]["_batch_index"] == 1

    def test_error_handling(self):
        """无效 payload 不应中断批量流程"""
        results = analyze_emails_batch([{}])
        assert len(results) == 1
        # 空 {} 不会抛异常，analyze_email 能处理
        assert "error" not in results[0]

    def test_mixed_valid_invalid(self):
        """有效和无效邮件混杂应正确处理"""
        results = analyze_emails_batch([
            {"subject": "正常", "plainText": "test"},
            {"subject": "垃圾", "plainText": "恭喜中奖"},
        ])
        assert len(results) == 2

    def test_spam_label_in_batch(self):
        """批量中应保留垃圾邮件标记"""
        results = analyze_emails_batch([{
            "subject": "恭喜中奖",
            "plainText": "免费领取大奖",
        }])
        assert results[0]["spam"]["label"] == "spam"

    def test_normal_label_in_batch(self):
        """批量中正常邮件应标记为 normal"""
        results = analyze_emails_batch([{
            "subject": "周报",
            "plainText": "本周工作正常",
        }])
        assert results[0]["spam"]["label"] == "normal"


class TestBatchSummary:
    """测试批量结果统计。"""

    def test_empty_results(self):
        summary = batch_summary([])
        assert summary["total"] == 0
        assert summary["spam_count"] == 0
        assert summary["spam_rate"] == 0.0

    def test_single_spam(self):
        results = analyze_emails_batch([{
            "subject": "恭喜中奖",
            "plainText": "免费领取大奖",
        }])
        summary = batch_summary(results)
        assert summary["total"] == 1
        assert summary["spam_count"] == 1
        assert summary["spam_rate"] == 1.0

    def test_single_normal(self):
        results = analyze_emails_batch([{
            "subject": "周报",
            "plainText": "本周工作正常",
        }])
        summary = batch_summary(results)
        assert summary["total"] == 1
        assert summary["spam_count"] == 0
        assert summary["spam_rate"] == 0.0

    def test_risk_level_distribution(self):
        results = analyze_emails_batch([
            {"subject": "正常", "plainText": "test"},
            {"subject": "紧急", "plainText": "请立即处理"},
        ])
        summary = batch_summary(results)
        assert "risk_level_distribution" in summary
        assert isinstance(summary["risk_level_distribution"], dict)

    def test_action_counts(self):
        """应统计 action 触发次数"""
        results = analyze_emails_batch([{
            "subject": "紧急故障",
            "plainText": "请立即审批处理",
        }])
        summary = batch_summary(results)
        assert isinstance(summary["action_counts"], dict)

    def test_high_priority_count(self):
        """应统计高优先级邮件数"""
        results = analyze_emails_batch([{
            "subject": "紧急故障",
            "plainText": "请立即审批",
        }])
        summary = batch_summary(results)
        assert summary["high_priority_count"] >= 1


class TestAnalyzeWithProgress:
    """测试带进度回调的批量分析。"""

    def test_no_callback(self):
        """不传 callback 应正常工作"""
        results = analyze_with_progress([{"subject": "test", "plainText": "hi"}])
        assert len(results) == 1

    def test_callback_invoked(self):
        """callback 应被正确调用"""
        calls = []

        def progress(current, total):
            calls.append((current, total))

        results = analyze_with_progress([
            {"subject": "A", "plainText": "a"},
            {"subject": "B", "plainText": "b"},
        ], callback=progress)
        assert len(calls) == 2
        assert calls[-1] == (2, 2)  # 最后一次调用

    def test_callback_error_handling(self):
        """callback 抛异常不应影响分析"""

        def broken_callback(current, total):
            raise ValueError("callback error")

        results = analyze_with_progress([
            {"subject": "test", "plainText": "hi"},
        ], callback=broken_callback)
        assert len(results) == 1

    def test_batch_index_in_progress(self):
        """带进度回调的结果应包含 _batch_index"""
        results = analyze_with_progress([
            {"subject": "A", "plainText": "a"},
        ])
        assert results[0]["_batch_index"] == 0


class TestAnalyzeBatchWithConfig:
    """测试自定义配置批量分析。"""

    def test_default_config(self):
        """不传配置应使用默认配置"""
        results = analyze_batch_with_config([{"subject": "test", "plainText": "hi"}])
        assert len(results) == 1
        assert "_config" in results[0]

    def test_custom_config(self):
        """自定义配置应生效"""
        config = PluginConfig(spam_threshold=0.9)
        results = analyze_batch_with_config(
            [{"subject": "test", "plainText": "hi"}],
            config=config,
        )
        assert results[0]["_config"]["spam_threshold"] == 0.9

    def test_config_to_dict(self):
        """配置信息应包含所有字段"""
        results = analyze_batch_with_config([{"subject": "test", "plainText": "hi"}])
        config = results[0]["_config"]
        assert "spam_threshold" in config
        assert "enable_link_detection" in config
        assert "homoglyph_sensitivity" in config

    def test_empty_payloads_with_config(self):
        """空 payload 列表应返回空列表"""
        results = analyze_batch_with_config([])
        assert results == []
