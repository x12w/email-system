from __future__ import annotations

import re
from typing import Any

import dns.resolver


# ============================================================
# 邮件头分析模块
# ============================================================
#
# 邮件头（Email Headers）包含了邮件的"元数据"——谁发的、
# 经过了哪些服务器、有没有通过认证等。分析邮件头可以发现
# 很多安全线索。
#
# 重要的邮件头字段：
#   - From:         发件人地址（易伪造）
#   - Reply-To:     回复地址（攻击者常设为不同地址来截获回复）
#   - Return-Path:  退信地址（应该和 From 一致）
#   - Received:     邮件经过的服务器链（跟踪邮件真实来源）
#   - SPF:          发件人策略框架（Sender Policy Framework）
#   - DKIM:         域名密钥识别邮件（DomainKeys Identified Mail）
#   - DMARC:        基于域名的消息认证报告和一致性
#   - Message-ID:   邮件的唯一 ID
#   - Date:         邮件发送时间
#
# 注意：当前插件传入的 payload 可能不包含原始邮件头。
# 这些函数在提供了邮件头数据时使用，没有时返回空结果。


# 常见的邮件认证头名称
_AUTH_RESULTS_HEADER = "Authentication-Results"
_SPF_HEADER = "Received-SPF"
_DKIM_HEADER = "DKIM-Signature"


def parse_authentication_results(
    headers: dict[str, str],
) -> dict[str, str]:
    """解析邮件认证结果头（Authentication-Results）。

    Authentication-Results 头是由收件服务器在收信时添加的，
    记录了 SPF、DKIM、DMARC 的验证结果。
    它的格式通常是：

        Authentication-Results: mx.example.com;
            spf=pass smtp.mailfrom=user@example.com;
            dkim=pass header.d=example.com;
            dmarc=pass header.from=example.com

    Args:
        headers: 邮件头字典，键为头字段名（不区分大小写），值为字段值

    Returns:
        解析后的认证结果字典，包含 spf、dkim、dmarc 三个键，
        值可能为 "pass"、"fail"、"softfail"、"neutral"、"none" 或 "unknown"
    """
    result: dict[str, str] = {
        "spf": "unknown",
        "dkim": "unknown",
        "dmarc": "unknown",
    }

    if not headers:
        return result

    # 查找认证结果头（可能有多个，取第一个）
    auth_value = None
    for key, value in headers.items():
        if key.lower() == "authentication-results":
            auth_value = value
            break

    if not auth_value:
        return result

    auth_lower = auth_value.lower()

    # 用正则提取 spf/dkim/dmarc 的结果
    # spf=pass, spf=fail 等
    spf_match = re.search(r"spf\s*=\s*(\w+)", auth_lower)
    if spf_match:
        result["spf"] = spf_match.group(1)

    dkim_match = re.search(r"dkim\s*=\s*(\w+)", auth_lower)
    if dkim_match:
        result["dkim"] = dkim_match.group(1)

    dmarc_match = re.search(r"dmarc\s*=\s*(\w+)", auth_lower)
    if dmarc_match:
        result["dmarc"] = dmarc_match.group(1)

    return result


def _query_txt_record(query_domain: str) -> list[str]:
    """查询域名的 TXT 记录。

    TXT 记录是 DNS 中一种可以存储任意文本的记录类型。
    SPF、DKIM、DMARC 都使用 TXT 记录来发布策略和密钥。

    Args:
        query_domain: 要查询的域名

    Returns:
        TXT 记录值列表（每个元素是一条 TXT 记录的内容）
    """
    try:
        answers = dns.resolver.resolve(query_domain, "TXT")
        return [str(answer).strip('"') for answer in answers]
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return []
    except dns.exception.DNSException:
        return []


def check_spf(domain: str, ip: str | None = None) -> dict[str, Any]:
    """检查 SPF（发件人策略框架）。

    SPF 的作用：
    域名所有者可以在 DNS 中发布 SPF 记录，声明哪些 IP 地址
    被允许使用该域名发送邮件。

    检查方式：
    查询域名下的 TXT 记录，找到以 "v=spf1" 开头的记录。
    如果存在 SPF 记录，说明域名配置了 SPF（不一定 pass）。
    如果不存在，说明域名没有 SPF 保护。

    Args:
        domain: 发件域名（如 "gmail.com"）
        ip:     发件服务器 IP 地址（可选，用于进一步验证）

    Returns:
        检查结果字典，包含：
        - checked:   是否实际进行了检查
        - result:    检查结果（"pass" / "fail" / "not_found"）
        - spf_record: SPF 记录内容（如存在）
        - message:   结果说明
    """
    if not domain:
        return {
            "checked": False, "result": "not_checked",
            "spf_record": "", "message": "未提供域名",
        }

    domain_lower = domain.lower().strip()
    records = _query_txt_record(domain_lower)

    # 查找以 "v=spf1" 开头的 SPF 记录
    spf_records = [r for r in records if r.startswith("v=spf1")]
    if spf_records:
        spf_text = spf_records[0]
        return {
            "checked": True,
            "result": "found",
            "spf_record": spf_text,
            "message": f"域名 '{domain}' 配置了 SPF 记录",
        }

    return {
        "checked": True,
        "result": "not_found",
        "spf_record": "",
        "message": f"域名 '{domain}' 没有 SPF 记录，可能存在伪造风险",
    }


def check_dkim(domain: str, selector: str | None = None) -> dict[str, Any]:
    """检查 DKIM（域名密钥识别邮件）。

    DKIM 的作用：
    发件服务器用私钥给邮件签名，收件服务器通过 DNS 获取公钥
    来验证签名。

    检查方式：
    DNS 查询格式为：<selector>._domainkey.<domain>
    常用选择器有 "default"、"google"、"dkim"、"20230601" 等。

    注意：真正的 DKIM 验证需要完整的签名内容，这里只检查
    公钥记录是否存在。

    Args:
        domain:   发件域名
        selector: DKIM 选择器（默认尝试常见选择器）

    Returns:
        检查结果字典
    """
    if not domain:
        return {
            "checked": False, "result": "not_checked",
            "dkim_record": "", "message": "未提供域名",
        }

    domain_lower = domain.lower().strip()
    # 如果没有提供选择器，尝试常见的选择器列表
    selectors_to_try = [selector] if selector else ["default", "google", "dkim",
                                                     "20230601", "mx", "k1"]

    for sel in selectors_to_try:
        if not sel:
            continue
        query = f"{sel}._domainkey.{domain_lower}"
        records = _query_txt_record(query)
        dkim_records = [r for r in records if "v=dkim1" in r.lower()]
        if dkim_records:
            return {
                "checked": True,
                "result": "found",
                "dkim_record": dkim_records[0],
                "selector": sel,
                "message": f"域名 '{domain}' 配置了 DKIM（选择器: {sel}）",
            }

    return {
        "checked": True,
        "result": "not_found",
        "dkim_record": "",
        "selector": selector or "default",
        "message": f"域名 '{domain}' 未找到 DKIM 记录",
    }


def check_dmarc(domain: str) -> dict[str, Any]:
    """检查 DMARC（基于域名的消息认证报告和一致性）。

    DMARC 的作用：
    在 SPF 和 DKIM 的基础上，DMARC 告诉收件服务器验证失败时
    应该怎么做。

    检查方式：
    DNS 查询 _dmarc.<domain> 的 TXT 记录。
    策略值 p=reject 最严格，p=quarantine 中等，p=none 仅监控。

    Args:
        domain: 发件域名

    Returns:
        检查结果字典
    """
    if not domain:
        return {
            "checked": False, "result": "not_checked",
            "dmarc_record": "", "policy": "", "message": "未提供域名",
        }

    domain_lower = domain.lower().strip()
    query = f"_dmarc.{domain_lower}"
    records = _query_txt_record(query)

    dmarc_records = [r for r in records if r.startswith("v=DMARC1")]
    if dmarc_records:
        dmarc_text = dmarc_records[0]
        # 提取策略值 p=reject / p=quarantine / p=none
        policy = ""
        policy_match = re.search(r"\bp\s*=\s*(\w+)", dmarc_text)
        if policy_match:
            policy = policy_match.group(1)
        return {
            "checked": True,
            "result": "found",
            "dmarc_record": dmarc_text,
            "policy": policy,
            "message": f"域名 '{domain}' 配置了 DMARC（策略: {policy}）",
        }

    return {
        "checked": True,
        "result": "not_found",
        "dmarc_record": "",
        "policy": "",
        "message": f"域名 '{domain}' 没有 DMARC 记录",
    }


def _extract_domain(addr: str) -> str:
    """从邮箱地址中提取 @ 后面的域名。

    Args:
        addr: 邮箱地址（如 "user@example.com"）

    Returns:
        域名部分（如 "example.com"），无 @ 时返回空字符串
    """
    at_pos = addr.rfind("@")
    if at_pos == -1:
        return ""
    return addr[at_pos + 1:].lower().strip()


def detect_reply_to_spoofing(
    from_addr: str,
    reply_to: str | None,
) -> dict[str, Any]:
    """检测 Reply-To 地址是否和 From 地址不一致。

    攻击者常用的手法：
    把 From 设为 victim@company.com，但把 Reply-To 设为自己的
    邮箱 attacker@evil.com。这样收件人回复邮件时，回复会发到
    攻击者那里，而真正的发件人收不到回复。

    Args:
        from_addr: 发件人地址
        reply_to:  Reply-To 地址（可能为 None）

    Returns:
        检测结果字典
    """
    result: dict[str, Any] = {
        "is_suspicious": False,
        "from_addr": from_addr,
        "reply_to": reply_to,
        "reason": "",
    }

    if not reply_to:
        return result

    from_domain = _extract_domain(from_addr)
    reply_domain = _extract_domain(reply_to)

    if not from_domain and not reply_domain:
        return result

    if from_domain != reply_domain:
        result["is_suspicious"] = True
        result["reason"] = (
            f"Reply-To 域名 '{reply_domain}' 与 From 域名 "
            f"'{from_domain}' 不一致，可能会被用于截获回复"
        )

    return result


def detect_missing_message_id(headers: dict[str, str]) -> dict[str, Any]:
    """检测邮件是否缺少 Message-ID。

    正常的邮件通常都有 Message-ID（邮件的唯一标识）。
    垃圾邮件和自动发送的邮件有时会缺少这个字段。

    Args:
        headers: 邮件头字典

    Returns:
        检测结果字典
    """
    if not headers:
        return {"has_message_id": False, "is_suspicious": True}

    has_id = any(
        key.lower() == "message-id" and bool(value.strip())
        for key, value in headers.items()
    )

    return {
        "has_message_id": has_id,
        "is_suspicious": not has_id,
    }


def analyze_headers(headers: dict[str, str]) -> dict[str, Any]:
    """综合分析邮件头，返回完整的检测结果。

    这个函数一次性执行所有邮件头分析，把结果汇总在一起。

    Args:
        headers: 邮件头字典

    Returns:
        分析结果字典，包含所有邮件头相关检测的结果
    """
    if not headers:
        return {
            "authentication": parse_authentication_results({}),
            "reply_to_check": {"is_suspicious": False, "reason": "无邮件头数据"},
            "message_id_check": detect_missing_message_id({}),
            "spf_result": check_spf(""),
            "dkim_result": check_dkim(""),
            "dmarc_result": check_dmarc(""),
        }

    return {
        "authentication": parse_authentication_results(headers),
        "reply_to_check": detect_reply_to_spoofing(
            headers.get("From", ""),
            headers.get("Reply-To"),
        ),
        "message_id_check": detect_missing_message_id(headers),
        "spf_result": check_spf(_extract_domain(headers.get("From", ""))),
        "dkim_result": check_dkim(_extract_domain(headers.get("From", ""))),
        "dmarc_result": check_dmarc(_extract_domain(headers.get("From", ""))),
    }
