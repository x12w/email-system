from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuleHit:
    type: str
    value: str
    risk_level: str
    reason: str


def analyze_email(payload: dict[str, Any]) -> dict[str, Any]:
    subject = str(payload.get("subject") or "")
    plain_text = str(payload.get("plainText") or "")
    links = payload.get("links") or []

    text = f"{subject}\n{plain_text}".lower()
    high_priority_score = _score_keywords(text, ["urgent", "紧急", "审批", "故障", "投诉", "合同", "到期"])
    spam_score = _score_keywords(text, ["中奖", "免费", "返利", "贷款", "casino", "winner"])
    indicators = _detect_link_risks(links)

    risk_score = min(1.0, 0.25 * len(indicators))
    risk_level = "none"
    if risk_score >= 0.75:
        risk_level = "high"
    elif risk_score >= 0.5:
        risk_level = "medium"
    elif risk_score > 0:
        risk_level = "low"

    priority_label = "high" if high_priority_score >= 0.5 else "normal"
    spam_label = "spam" if spam_score >= 0.6 else "normal"

    actions: list[str] = []
    if priority_label == "high" and spam_label != "spam":
        actions.append("mark_high_priority")
        actions.append("push_notification")
    if risk_level in {"high", "critical"}:
        actions.append("push_security_alert")

    return {
        "pluginVersion": "0.1.0",
        "spam": {"label": spam_label, "score": spam_score},
        "priority": {
            "label": priority_label,
            "score": high_priority_score,
            "reasons": ["keyword match"] if priority_label == "high" else [],
        },
        "risk": {
            "level": risk_level,
            "score": risk_score,
            "indicators": [hit.__dict__ for hit in indicators],
        },
        "actions": actions,
    }


def _score_keywords(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    hits = sum(1 for keyword in keywords if keyword.lower() in text)
    return min(1.0, hits / 2)


def _detect_link_risks(links: list[Any]) -> list[RuleHit]:
    hits: list[RuleHit] = []
    for raw_link in links:
        link = str(raw_link)
        lowered = link.lower()
        if "://" in lowered and _looks_like_ip_url(lowered):
            hits.append(RuleHit("url", link, "medium", "url uses ip address host"))
        if any(domain in lowered for domain in ["bit.ly", "tinyurl.com", "t.co"]):
            hits.append(RuleHit("url", link, "low", "short link requires expansion"))
        if any(word in lowered for word in ["login", "password", "pay", "verify"]):
            hits.append(RuleHit("url", link, "medium", "sensitive action keyword in url"))
    return hits


def _looks_like_ip_url(link: str) -> bool:
    host = link.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    parts = host.split(".")
    return len(parts) == 4 and all(part.isdigit() for part in parts)

