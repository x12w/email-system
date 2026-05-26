from __future__ import annotations

import json

from analyzer import analyze_email


def analyze_email_json(request_json: str) -> str:
    try:
        payload = json.loads(request_json)
        result = analyze_email(payload)
        return json.dumps(result, ensure_ascii=False)
    except Exception as exc:
        return json.dumps(
            {
                "pluginVersion": "0.1.0",
                "spam": {"label": "unknown", "score": 0.0},
                "priority": {"label": "normal", "score": 0.0, "reasons": []},
                "risk": {"level": "none", "score": 0.0, "indicators": []},
                "actions": [],
                "error": str(exc),
            },
            ensure_ascii=False,
        )

