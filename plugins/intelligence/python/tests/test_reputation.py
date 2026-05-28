from __future__ import annotations

from unittest.mock import patch

import pytest

from src.reputation import (
    check_domain_age,
    check_domain_reputation,
    check_ip_reputation,
)


class TestCheckDomainReputation:
    """测试域名声誉检查。"""

    def test_empty_domain(self):
        result = check_domain_reputation("")
        assert result["score"] == 0.0
        assert result["listed"] is False
        assert result["blacklists"] == []

    def test_whitelisted_domain(self):
        """白名单中的域名得分应为 0.0"""
        result = check_domain_reputation("gmail.com")
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_blacklisted_domain(self):
        """本地黑名单中的域名应被标记"""
        result = check_domain_reputation("spam.com")
        assert result["score"] > 0.5
        assert result["listed"] is True
        assert "local_blacklist" in result["blacklists"]

    def test_blacklisted_domain_2(self):
        result = check_domain_reputation("spammer.com")
        assert result["listed"] is True
        assert result["score"] == 0.8

    def test_blacklisted_domain_3(self):
        result = check_domain_reputation("marketing-spam.com")
        assert result["listed"] is True

    def test_whitelist_vs_blacklist_precedence(self):
        """白名单优先于黑名单"""
        # google.com 在白名单中，即使逻辑上匹配黑名单模式
        result = check_domain_reputation("google.com")
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_unknown_domain_needs_network(self):
        """未知域名需网络请求 DP; 至少不抛异常"""
        try:
            result = check_domain_reputation("example.com")
            assert "score" in result
            assert "details" in result
        except OSError:
            pytest.skip("网络不可用")


class TestCheckIpReputation:
    """测试 IP 声誉检查。"""

    def test_empty_ip(self):
        result = check_ip_reputation("")
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_valid_ip_no_listing(self):
        """有效 IP 但不在黑名单中（集成测试，需网络）"""
        try:
            # 使用 1.1.1.1（Cloudflare 的 DNS）——不在黑名单中
            result = check_ip_reputation("1.1.1.1")
            assert "score" in result
            assert "details" in result
        except OSError:
            pytest.skip("网络不可用")

    def test_invalid_ip_format(self):
        """IP 格式错误不应抛异常"""
        try:
            result = check_ip_reputation("999.999.999.999")
            assert "score" in result
        except OSError:
            pytest.skip("网络不可用")

    def test_private_ip_not_listed(self):
        """私有 IP 应不在黑名单中"""
        try:
            result = check_ip_reputation("10.0.0.1")
            assert result["score"] == 0.0
        except OSError:
            pytest.skip("网络不可用")


class TestCheckDomainAge:
    """测试域名年龄检查（占位实现）。"""

    def test_age_not_implemented(self):
        """当前返回 -1 表示未实现"""
        result = check_domain_age("example.com")
        assert result["age_days"] == -1
        assert result["is_new"] is False
        assert "未实现" in result["details"]
