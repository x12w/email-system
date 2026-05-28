from __future__ import annotations

import socket
from typing import Any

import dns.resolver


# ============================================================
# 域名和 IP 声誉检查模块
# ============================================================
#
# 声誉检查（Reputation Check）是垃圾邮件过滤的重要方法之一。
# 如果一个域名或 IP 地址曾经发送过大量垃圾邮件，它就会被
# 列入"黑名单"，以后从该地址发来的邮件都会被标记为可疑。
#
# 核心检测方法：DNSBL（DNS-based Blackhole List）
#   工作原理是把要查询的 IP 反转后拼上黑名单域名，然后做 DNS 查询。
#   如果 DNS 能查到结果（有 A 记录），说明该 IP 在黑名单中。
#   例如：查询 192.168.1.1 是否在 zen.spamhaus.org 中：
#     1. 反转 IP：1.1.168.192
#     2. 拼接域名：1.1.168.192.zen.spamhaus.org
#     3. DNS 查询：如果有 A 记录 → 被列入黑名单


# 公共 DNS 黑名单域名
_PUBLIC_DNSBL = [
    "zen.spamhaus.org",           # Spamhaus —— 最知名的 DNSBL 之一
    "bl.spamcop.net",             # SpamCop —— 基于用户投诉
    "dnsbl.sorbs.net",            # SORBS —— 综合黑名单
    "b.barracudacentral.org",     # Barracuda —— 知名安全厂商
]

# 已知的垃圾邮件发送域名（静态示例，仅用于演示）
_KNOWN_SPAM_DOMAINS = frozenset({
    "spam.com",
    "spammer.com",
    "marketing-spam.com",
})

# 已知的合法域名（白名单）
_KNOWN_LEGITIMATE_DOMAINS = frozenset({
    "google.com", "gmail.com",
    "microsoft.com", "outlook.com",
    "apple.com", "icloud.com",
    "amazon.com",
    "github.com",
    "zoom.us",
})


def _query_dnsbl(ip_address: str, dnsbl_domain: str) -> bool:
    """查询一个 IP 是否在指定的 DNSBL 黑名单中。

    DNSBL 的查询原理：
    正常的 DNS 查询是把域名解析成 IP（正向），而 DNSBL 反过来——
    把 IP 反转后拼上黑名单域名，如果能查到 A 记录说明 IP 被列入了黑名单。

    例如查询 192.168.1.1 是否在 zen.spamhaus.org 中：
    → DNS 查询 1.1.168.192.zen.spamhaus.org 的 A 记录
    → 如果查到结果 → 被列入黑名单
    → 如果查不到（NXDOMAIN）→ 不在黑名单中

    Args:
        ip_address:   要查询的 IP 地址（如 "192.168.1.1"）
        dnsbl_domain: DNSBL 域名（如 "zen.spamhaus.org"）

    Returns:
        True 表示 IP 在该黑名单中，False 表示不在
    """
    # 把 IP 反转：192.168.1.1 → 1.1.168.192
    parts = ip_address.strip().split(".")
    reversed_ip = ".".join(reversed(parts))
    query = f"{reversed_ip}.{dnsbl_domain}"

    try:
        # 用 dnspython 做 A 记录查询
        # 如果查到结果（有 A 记录），说明 IP 在黑名单中
        answers = dns.resolver.resolve(query, "A")
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        # NXDOMAIN：域名不存在 → 不在黑名单
        # NoAnswer：没有 A 记录 → 不在黑名单
        # Timeout：查询超时 → 网络问题，保守起见返回 False
        return False
    except dns.exception.DNSException:
        # 其他 DNS 异常，保守返回 False
        return False


def _query_dnsbl_multi(ip_address: str, dnsbl_list: list[str]) -> list[str]:
    """查询一个 IP 是否在多个 DNSBL 黑名单中。

    Args:
        ip_address:   要查询的 IP 地址
        dnsbl_list:   DNSBL 域名列表

    Returns:
        命中的黑名单域名列表（空列表表示不在任何黑名单中）
    """
    hit_list: list[str] = []
    for dnsbl in dnsbl_list:
        if _query_dnsbl(ip_address, dnsbl):
            hit_list.append(dnsbl)
    return hit_list


def check_domain_reputation(domain: str) -> dict[str, Any]:
    """检查域名声誉。

    通过 DNS 黑名单查询和本地黑名单两种方式检查域名声誉。

    查询流程：
    1. 先查本地白名单——如果域名在白名单中，直接返回"可信"
    2. 再查本地黑名单——如果域名在黑名单中，返回"可疑"
    3. 最后查 DNS 黑名单——需要网络请求

    Args:
        domain: 要检查的域名（如 "spammer.com"）

    Returns:
        检查结果字典，包含：
        - score:       声誉评分（0.0 可信 ~ 1.0 可疑）
        - listed:      是否在黑名单中
        - blacklists:  被哪些黑名单收录
        - details:     详细信息
    """
    result: dict[str, Any] = {
        "score": 0.0,
        "listed": False,
        "blacklists": [],
        "details": "",
    }

    if not domain:
        return result

    domain_lower = domain.lower().strip()

    # 1. 检查白名单
    if domain_lower in _KNOWN_LEGITIMATE_DOMAINS:
        result["score"] = 0.0
        result["details"] = f"域名 '{domain}' 在白名单中"
        return result

    # 2. 检查本地黑名单
    if domain_lower in _KNOWN_SPAM_DOMAINS:
        result["score"] = 0.8
        result["listed"] = True
        result["blacklists"].append("local_blacklist")
        result["details"] = f"域名 '{domain}' 在本地黑名单中"
        return result

    # 3. 如果不在本地黑名单/白名单中，查 DNSBL
    # 先解析域名拿到 IP，再用 IP 查 DNSBL
    try:
        ip_result = socket.gethostbyname(domain_lower)
        hit_list = _query_dnsbl_multi(ip_result, _PUBLIC_DNSBL)
        if hit_list:
            result["score"] = 0.8
            result["listed"] = True
            result["blacklists"] = hit_list
            result["details"] = (
                f"域名 '{domain}' (IP: {ip_result}) 在以下 DNSBL 中: "
                f"{', '.join(hit_list)}"
            )
        else:
            result["score"] = 0.1
            result["details"] = (
                f"域名 '{domain}' (IP: {ip_result}) 不在已知黑名单中，声誉良好"
            )
    except socket.gaierror:
        result["details"] = f"无法解析域名 '{domain}'"
    return result


def check_ip_reputation(ip_address: str) -> dict[str, Any]:
    """检查 IP 地址声誉。

    通过 DNS 黑名单查询 IP 是否被标记为垃圾邮件发送源。

    Args:
        ip_address: 要检查的 IP 地址（如 "192.168.1.1"）

    Returns:
        检查结果字典，同 check_domain_reputation
    """
    result: dict[str, Any] = {
        "score": 0.0,
        "listed": False,
        "blacklists": [],
        "details": "",
    }

    if not ip_address:
        return result

    # 直接查 DNSBL（不需要先解析域名，IP 本身就是地址）
    hit_list = _query_dnsbl_multi(ip_address, _PUBLIC_DNSBL)
    if hit_list:
        result["score"] = 0.8
        result["listed"] = True
        result["blacklists"] = hit_list
        result["details"] = (
            f"IP '{ip_address}' 在以下 DNSBL 中: {', '.join(hit_list)}"
        )
    else:
        result["details"] = f"IP '{ip_address}' 不在已知黑名单中"
    return result


def check_domain_age(domain: str) -> dict[str, Any]:
    """检查域名的注册时长。

    新注册的域名发送垃圾邮件的概率更高。
    通常，注册时间不到 30 天的域名需要特别警惕。

    注意：真正的域名年龄查询需要 WHOIS 请求。
    这里是一个接口定义。

    Args:
        domain: 要检查的域名

    Returns:
        检查结果字典：
        - age_days:    域名注册天数（-1 表示未知）
        - is_new:      是否是新注册域名
        - details:     详细信息
    """
    # TODO: 实现 WHOIS 查询
    return {
        "age_days": -1,
        "is_new": False,
        "details": "域名年龄查询需要 WHOIS 请求，当前未实现",
    }
