from __future__ import annotations

from unittest.mock import patch

import pytest

from src.header_analyzer import (
    analyze_headers,
    check_dkim,
    check_dmarc,
    check_spf,
    detect_missing_message_id,
    detect_reply_to_spoofing,
    parse_authentication_results,
)


class TestParseAuthenticationResults:
    """测试 Authentication-Results 解析。"""

    def test_empty_headers(self):
        """空字典应返回全 unknown"""
        result = parse_authentication_results({})
        assert result == {"spf": "unknown", "dkim": "unknown", "dmarc": "unknown"}

    def test_none_headers(self):
        result = parse_authentication_results(None)
        assert result == {"spf": "unknown", "dkim": "unknown", "dmarc": "unknown"}

    def test_no_auth_header(self):
        """没有 Authentication-Results 头应返回全 unknown"""
        result = parse_authentication_results({"From": "a@b.com"})
        assert result == {"spf": "unknown", "dkim": "unknown", "dmarc": "unknown"}

    def test_spf_pass(self):
        result = parse_authentication_results({
            "Authentication-Results": "mx.example.com; spf=pass smtp.mailfrom=user@example.com"
        })
        assert result["spf"] == "pass"

    def test_all_pass(self):
        result = parse_authentication_results({
            "Authentication-Results": (
                "mx.example.com; spf=pass smtp.mailfrom=user@example.com;"
                " dkim=pass header.d=example.com;"
                " dmarc=pass header.from=example.com"
            )
        })
        assert result["spf"] == "pass"
        assert result["dkim"] == "pass"
        assert result["dmarc"] == "pass"

    def test_spf_fail(self):
        result = parse_authentication_results({
            "Authentication-Results": "mx.example.com; spf=fail"
        })
        assert result["spf"] == "fail"

    def test_mixed_results(self):
        result = parse_authentication_results({
            "Authentication-Results": "mx.example.com; spf=pass; dkim=fail; dmarc=softfail"
        })
        assert result["spf"] == "pass"
        assert result["dkim"] == "fail"
        assert result["dmarc"] == "softfail"

    def test_case_insensitive_header_name(self):
        """头字段名不区分大小写"""
        result = parse_authentication_results({
            "authentication-results": "spf=pass"
        })
        assert result["spf"] == "pass"

    def test_partial_results(self):
        """部分结果——仅 SPF 有值，其他保持 unknown"""
        result = parse_authentication_results({
            "Authentication-Results": "spf=pass"
        })
        assert result["spf"] == "pass"
        assert result["dkim"] == "unknown"
        assert result["dmarc"] == "unknown"

    def test_spf_with_spaces(self):
        """spf= 周围允许有空格"""
        result = parse_authentication_results({
            "Authentication-Results": "spf = pass"
        })
        assert result["spf"] == "pass"


class TestDetectReplyToSpoofing:
    """测试 Reply-To 伪造检测。"""

    def test_no_reply_to(self):
        """没有 Reply-To 不应标记为可疑"""
        result = detect_reply_to_spoofing("user@example.com", None)
        assert result["is_suspicious"] is False

    def test_same_domain(self):
        """相同域名不应标记"""
        result = detect_reply_to_spoofing("user@example.com", "reply@example.com")
        assert result["is_suspicious"] is False

    def test_different_domain(self):
        """不同域名应标记为可疑"""
        result = detect_reply_to_spoofing("user@company.com", "attacker@evil.com")
        assert result["is_suspicious"] is True
        assert "不一致" in result["reason"]

    def test_both_empty(self):
        result = detect_reply_to_spoofing("", "user@example.com")
        # from_domain 为空，reply_domain 有值
        assert result["is_suspicious"] is True

    def test_invalid_email_no_at(self):
        result = detect_reply_to_spoofing("invalid", None)
        assert result["is_suspicious"] is False

    def test_case_insensitive_domain(self):
        """域名比较应不区分大小写"""
        result = detect_reply_to_spoofing("user@Example.com", "reply@example.com")
        assert result["is_suspicious"] is False

    def test_empty_reply_to_string(self):
        """空字符串 Reply-To 不应标记"""
        result = detect_reply_to_spoofing("user@example.com", "")
        assert result["is_suspicious"] is False


class TestDetectMissingMessageId:
    """测试 Message-ID 检测。"""

    def test_no_headers(self):
        result = detect_missing_message_id(None)
        assert result["is_suspicious"] is True
        assert result["has_message_id"] is False

    def test_empty_headers(self):
        result = detect_missing_message_id({})
        assert result["is_suspicious"] is True

    def test_has_message_id(self):
        result = detect_missing_message_id({"Message-ID": "<abc123@example.com>"})
        assert result["is_suspicious"] is False
        assert result["has_message_id"] is True

    def test_empty_message_id_value(self):
        """Message-ID 值为空时应视为缺失"""
        result = detect_missing_message_id({"Message-ID": ""})
        assert result["is_suspicious"] is True

    def test_case_insensitive(self):
        result = detect_missing_message_id({"message-id": "<abc@example.com>"})
        assert result["is_suspicious"] is False

    def test_whitespace_only_message_id(self):
        """Message-ID 只含空白应视为缺失"""
        result = detect_missing_message_id({"Message-ID": "   "})
        assert result["is_suspicious"] is True


class TestCheckSpf:
    """测试 SPF 检查。"""

    def test_empty_domain(self):
        result = check_spf("")
        assert result["checked"] is False
        assert result["result"] == "not_checked"

    def test_not_found_domain(self):
        """不存在的域名应返回 not_found"""
        result = check_spf("nonexistent-xyz-123456.com")
        assert result["checked"] is True
        assert result["result"] == "not_found"

    def test_well_known_domain(self):
        """知名域名应有 SPF 记录（集成测试，需网络）"""
        result = check_spf("gmail.com")
        if result["result"] == "not_found":
            pytest.skip("DNS TXT 查询不可用")
        assert result["checked"] is True
        assert result["result"] == "found"
        assert result["spf_record"].startswith("v=spf1")

    def test_spf_record_field(self):
        """返回的记录字段应包含 SPF 内容（集成测试）"""
        result = check_spf("gmail.com")
        if result["result"] == "not_found":
            pytest.skip("DNS TXT 查询不可用")
        assert "include" in result["spf_record"]


class TestCheckDkim:
    """测试 DKIM 检查。"""

    def test_empty_domain(self):
        result = check_dkim("")
        assert result["checked"] is False
        assert result["result"] == "not_checked"

    def test_not_found(self):
        result = check_dkim("nonexistent-xyz-123456.com")
        assert result["checked"] is True
        assert result["result"] == "not_found"

    def test_google_dkim(self):
        """Google 的 DKIM 选择器 'google' 应有记录（集成测试）"""
        result = check_dkim("gmail.com", selector="google")
        if result["result"] == "not_found":
            pytest.skip("DNS TXT 查询不可用")
        assert result["checked"] is True
        assert result["result"] == "found"


class TestCheckDmarc:
    """测试 DMARC 检查。"""

    def test_empty_domain(self):
        result = check_dmarc("")
        assert result["checked"] is False
        assert result["result"] == "not_checked"

    def test_not_found(self):
        result = check_dmarc("nonexistent-xyz-123456.com")
        assert result["checked"] is True
        assert result["result"] == "not_found"

    def test_well_known_domain(self):
        """知名域名应有 DMARC 记录（集成测试）"""
        result = check_dmarc("gmail.com")
        if result["result"] == "not_found":
            pytest.skip("DNS TXT 查询不可用")
        assert result["checked"] is True
        assert result["result"] == "found"
        assert result["policy"] in ("reject", "quarantine", "none")

    def test_dmarc_policy_field(self):
        """DMARC 结果应包含 policy 字段（集成测试）"""
        result = check_dmarc("gmail.com")
        if result["result"] == "not_found":
            pytest.skip("DNS TXT 查询不可用")
        assert "policy" in result
        assert result["policy"]  # 非空


class TestCheckDkimCustomSelector:
    """测试自定义 DKIM 选择器。"""

    def test_custom_selector_empty_domain(self):
        result = check_dkim("", selector="custom")
        assert result["checked"] is False

    def test_selector_in_result(self):
        """返回结果应包含使用的选择器名"""
        result = check_dkim("outlook.com", selector="google")
        if result["result"] == "found":
            assert result["selector"] == "google"


class TestAnalyzeHeaders:
    """测试综合分析。"""

    def test_empty_headers(self):
        result = analyze_headers({})
        assert "authentication" in result
        assert "reply_to_check" in result
        assert "message_id_check" in result
        assert result["message_id_check"]["is_suspicious"] is True

    def test_none_headers(self):
        result = analyze_headers(None)
        assert result["message_id_check"]["is_suspicious"] is True

    def test_with_auth_header(self):
        result = analyze_headers({
            "Authentication-Results": "spf=pass",
            "From": "user@example.com",
            "Message-ID": "<abc@example.com>",
        })
        assert result["authentication"]["spf"] == "pass"
        assert result["message_id_check"]["has_message_id"] is True
        assert result["reply_to_check"]["is_suspicious"] is False
