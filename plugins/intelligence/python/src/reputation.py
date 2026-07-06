from __future__ import annotations

import json
import logging
import os
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
    """检查域名的注册时长。

    通过系统 whois 命令查询域名的 creation_date，计算注册天数。
    如果 whois 命令不可用或查询失败，返回占位结果。

    Args:
        domain: 要查询的域名

    Returns:
        检查结果字典：
        - age_days: 注册天数，-1 表示查询失败
        - is_new:   是否为新注册域名（< 30 天）
        - details:  结果说明
    """
    if not domain:
        return {"age_days": -1, "is_new": False, "details": "未提供域名"}

    try:
        proc = subprocess.run(
            ["whois", domain.strip()],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = proc.stdout
    except FileNotFoundError:
        logger.warning("whois 命令不可用，跳过域名年龄查询")
        return {"age_days": -1, "is_new": False, "details": "系统 whois 命令不可用"}
    except subprocess.TimeoutExpired:
        logger.warning("whois 查询超时: %s", domain)
        return {"age_days": -1, "is_new": False, "details": "WHOIS 查询超时"}
    except OSError as exc:
        logger.warning("whois 查询失败: %s: %s", domain, exc)
        return {"age_days": -1, "is_new": False, "details": f"WHOIS 查询失败: {exc}"}

    # 尝试多种常见的 creation_date 格式
    creation_date = _parse_whois_date(output)
    if creation_date is None:
        return {
            "age_days": -1,
            "is_new": False,
            "details": "无法从 WHOIS 记录中解析创建日期",
        }

    age = (datetime.now(timezone.utc) - creation_date).days
    is_new = age < 30

    return {
        "age_days": age,
        "is_new": is_new,
        "details": (
            f"域名 '{domain}' 注册于 {creation_date.strftime('%Y-%m-%d')}，"
            f"距今 {age} 天{'（新注册域名）' if is_new else ''}"
        ),
    }


def _parse_whois_date(whois_output: str) -> datetime | None:
    """从 WHOIS 输出中解析域名创建日期。

    尝试匹配多种常见格式：
    - Creation Date: 2023-01-15T10:30:00Z
    - created: 2023-01-15 10:30:00
    - Creation Date: 2023-01-15
    - created............: 2023-01-15

    Args:
        whois_output: WHOIS 命令的原始输出

    Returns:
        datetime 对象，解析失败返回 None
    """
    patterns = [
        r"(?:creation\s*date|created|registered)\s*[:.]?\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
        r"(?:creation\s*date|created|registered)\s*[:.]?\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
        r"(?:creation\s*date|created|registered)\s*[:.]?\s*(\d{4}-\d{2}-\d{2})",
        r"(?:creation\s*date|created|registered)\s*[:.]?\s*(\d{2}/\d{2}/\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, whois_output, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            try:
                if "T" in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(
                        tzinfo=timezone.utc
                    )
                if "/" in date_str:
                    return datetime.strptime(date_str, "%m/%d/%Y").replace(
                        tzinfo=timezone.utc
                    )
                if " " in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    )
                return datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                continue

    return None
