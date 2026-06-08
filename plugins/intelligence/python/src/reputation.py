from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json_list(filename: str) -> list[str]:
    """从 data/ 目录加载 JSON 数组文件。"""
    filepath = _DATA_DIR / filename
    if not filepath.is_file():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# 在模块加载时从 JSON 文件读取，支持在不改代码的前提下增删规则
_WHITELIST_DOMAINS = frozenset(_load_json_list("whitelist_domains.json"))
_BLACKLIST_DOMAINS = frozenset(_load_json_list("blacklist_domains.json"))
_DNSBL_SERVERS = _load_json_list("dnsbl_servers.json")


import dns.resolver


def _query_dnsbl(ip_address: str, dnsbl_domain: str) -> bool:
    """查询一个 IP 是否在指定的 DNSBL 黑名单中。

    DNSBL 的查询原理：
    正常的 DNS 查询是把域名解析成 IP（正向），而 DNSBL 反过来——
    把 IP 反转后拼上黑名单域名，如果能查到 A 记录说明 IP 被列入了黑名单。

    Args:
        ip_address:   要查询的 IP 地址
        dnsbl_domain: DNSBL 域名

    Returns:
        True 表示 IP 在该黑名单中，False 表示不在
    """
    parts = ip_address.strip().split(".")
    reversed_ip = ".".join(reversed(parts))
    query = f"{reversed_ip}.{dnsbl_domain}"

    try:
        answers = dns.resolver.resolve(query, "A")
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return False
    except dns.exception.DNSException:
        return False


def _query_dnsbl_multi(ip_address: str, dnsbl_list: list[str]) -> list[str]:
    """查询一个 IP 是否在多个 DNSBL 黑名单中。"""
    return [d for d in dnsbl_list if _query_dnsbl(ip_address, d)]


def check_domain_reputation(
    domain: str,
    *,
    whitelist: set[str] | None = None,
    blacklist: set[str] | None = None,
    dnsbl_servers: list[str] | None = None,
) -> dict[str, Any]:
    """检查域名声誉。

    支持可配置的白名单/黑名单/DNSBL 服务器列表，不传时使用 JSON 文件中的默认值。

    Args:
        domain:        要检查的域名
        whitelist:     可选的白名单集合
        blacklist:     可选的黑名单集合
        dnsbl_servers: 可选的 DNSBL 服务器列表

    Returns:
        检查结果字典
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
    wl = frozenset(whitelist) if whitelist is not None else _WHITELIST_DOMAINS
    bl = frozenset(blacklist) if blacklist is not None else _BLACKLIST_DOMAINS
    dnsbl = dnsbl_servers if dnsbl_servers is not None else _DNSBL_SERVERS

    # 1. 白名单
    if domain_lower in wl:
        result["score"] = 0.0
        result["details"] = f"域名 '{domain}' 在白名单中"
        return result

    # 2. 本地黑名单
    if domain_lower in bl:
        result["score"] = 0.8
        result["listed"] = True
        result["blacklists"].append("local_blacklist")
        result["details"] = f"域名 '{domain}' 在本地黑名单中"
        return result

    # 3. DNSBL
    if not dnsbl:
        result["score"] = 0.1
        result["details"] = "DNSBL 未配置，无法进行网络声誉检查"
        return result

    try:
        ip_result = socket.gethostbyname(domain_lower)
        hit_list = _query_dnsbl_multi(ip_result, dnsbl)
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


def check_ip_reputation(
    ip_address: str,
    *,
    dnsbl_servers: list[str] | None = None,
) -> dict[str, Any]:
    """检查 IP 地址声誉。

    支持可配置的 DNSBL 列表。

    Args:
        ip_address:   要检查的 IP 地址
        dnsbl_servers: 可选的 DNSBL 服务器列表

    Returns:
        检查结果字典
    """
    result: dict[str, Any] = {
        "score": 0.0,
        "listed": False,
        "blacklists": [],
        "details": "",
    }

    if not ip_address:
        return result

    dnsbl = dnsbl_servers if dnsbl_servers is not None else _DNSBL_SERVERS

    if not dnsbl:
        result["details"] = "DNSBL 未配置，无法进行 IP 声誉检查"
        return result

    hit_list = _query_dnsbl_multi(ip_address, dnsbl)
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
    """检查域名的注册时长（占位实现，需要 WHOIS 请求）。"""
    return {
        "age_days": -1,
        "is_new": False,
        "details": "域名年龄查询需要 WHOIS 请求，当前未实现",
    }
