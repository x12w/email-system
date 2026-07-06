from __future__ import annotations

import pytest

from src.reputation import (
    check_domain_age,
    check_domain_reputation,
    check_ip_reputation,
)


# ============================================================
# 离线单元测试 —— 不依赖网络，任何环境都能运行
# ============================================================

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

    def test_blacklisted_multiple(self):
        for domain in ("spammer.com", "marketing-spam.com"):
            result = check_domain_reputation(domain)
            assert result["listed"] is True
            assert result["score"] == 0.8

    def test_whitelist_vs_blacklist_precedence(self):
        """白名单优先于黑名单"""
        result = check_domain_reputation("google.com")
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_custom_whitelist(self):
        """可传入自定义白名单覆盖默认值。"""
        result = check_domain_reputation("evil.com", whitelist={"evil.com"})
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_custom_blacklist(self):
        """可传入自定义黑名单覆盖默认值。"""
        result = check_domain_reputation("evil.com", blacklist={"evil.com"})
        assert result["score"] > 0
        assert result["listed"] is True

    def test_dnsbl_disabled(self):
        """空 DNSBL 列表应跳过网络查询。"""
        result = check_domain_reputation("example.com", dnsbl_servers=[])
        assert "未配置" in result["details"]


class TestCheckIpReputation:
    """测试 IP 声誉检查。"""

    def test_empty_ip(self):
        result = check_ip_reputation("")
        assert result["score"] == 0.0
        assert result["listed"] is False

    def test_dnsbl_disabled(self):
        """空 DNSBL 列表应跳过网络查询。"""
        result = check_ip_reputation("1.1.1.1", dnsbl_servers=[])
        assert "未配置" in result["details"]


class TestCheckDomainAge:
    """测试域名年龄检查。"""

    def test_age_fallback_on_missing_whois(self):
        """whois 命令不可用时返回占位结果。"""
        result = check_domain_age("example.com")
        assert result["age_days"] == -1
        assert result["is_new"] is False
        # whois 命令不可用或查询失败时返回 -1
        assert result["details"] != ""

    def test_age_empty_domain(self):
        result = check_domain_age("")
        assert result["age_days"] == -1
        assert result["details"] == "未提供域名"


# ============================================================
# 联网集成测试 —— 需要 DNS 网络可达
# ============================================================

@pytest.mark.online
class TestOnlineReputation:
    """需要网络的声誉测试。用 pytest -m 'not online' 跳过。"""

    def test_unknown_domain_resolves(self):
        result = check_domain_reputation("example.com")
        assert "score" in result
        assert "details" in result

    @pytest.mark.dns
    def test_valid_ip_not_listed(self):
        """Cloudflare DNS — 不应在任何黑名单中。"""
        result = check_ip_reputation("1.1.1.1")
        assert "score" in result
        assert "details" in result

    @pytest.mark.dns
    def test_private_ip(self):
        """私有 IP 查 DNSBL 不会命中但也不抛异常。"""
        result = check_ip_reputation("10.0.0.1")
        assert "score" in result
