from __future__ import annotations

from src.config import DEFAULT_CONFIG, PluginConfig


class TestPluginConfig:
    """测试 PluginConfig 配置类。"""

    def test_default_values(self):
        """默认配置应使用正确的默认值"""
        config = PluginConfig()
        assert config.spam_threshold == 0.6
        assert config.priority_threshold == 0.5
        assert config.risk_indicator_weight == 0.25
        assert config.enable_link_detection is True
        assert config.enable_attachment_detection is True
        assert config.enable_sender_detection is True
        assert config.enable_phishing_detection is True
        assert config.enable_html_analysis is True
        assert config.enable_header_analysis is True
        assert config.enable_reputation_check is False
        assert config.homoglyph_sensitivity == 1.0
        assert config.typosquatting_max_edit_distance == 2

    def test_load_from_dict_partial(self):
        """部分覆盖应只修改指定字段"""
        config = PluginConfig.load_from_dict({"spam_threshold": 0.8})
        assert config.spam_threshold == 0.8
        assert config.priority_threshold == 0.5  # 保持默认

    def test_load_from_dict_full(self):
        """全量覆盖应正确设置所有字段"""
        config = PluginConfig.load_from_dict({
            "spam_threshold": 0.9,
            "enable_html_analysis": False,
            "enable_reputation_check": True,
        })
        assert config.spam_threshold == 0.9
        assert config.enable_html_analysis is False
        assert config.enable_reputation_check is True

    def test_load_from_dict_ignores_unknown_keys(self):
        """未知键应被忽略而非报错"""
        config = PluginConfig.load_from_dict({"unknown_key": 123})
        assert config.spam_threshold == 0.6  # 默认不变

    def test_load_from_dict_empty(self):
        """空字典应返回完全默认的配置"""
        config = PluginConfig.load_from_dict({})
        assert config == PluginConfig()

    def test_to_dict_contains_all_fields(self):
        """to_dict() 应返回包含所有配置项的字典"""
        config = PluginConfig()
        d = config.to_dict()
        assert d["spam_threshold"] == 0.6
        assert d["enable_link_detection"] is True
        assert d["homoglyph_sensitivity"] == 1.0
        assert len(d) == 14  # 所有配置项数量

    def test_to_dict_values_match(self):
        """to_dict() 的值应与配置实例一致"""
        config = PluginConfig(spam_threshold=0.9, enable_html_analysis=False)
        d = config.to_dict()
        assert d["spam_threshold"] == 0.9
        assert d["enable_html_analysis"] is False

    def test_default_config_global(self):
        """全局 DEFAULT_CONFIG 应为 PluginConfig 实例"""
        assert isinstance(DEFAULT_CONFIG, PluginConfig)
        assert DEFAULT_CONFIG.spam_threshold == 0.6

    def test_load_from_dict_round_trip(self):
        """load_from_dict 与 to_dict 应可互相转换"""
        config = PluginConfig(spam_threshold=0.7, enable_reputation_check=True)
        d = config.to_dict()
        restored = PluginConfig.load_from_dict(d)
        assert restored == config
