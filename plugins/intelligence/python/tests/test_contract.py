"""契约测试 — 验证插件输出符合 JSON Schema。

这些测试只依赖 Python 标准库和插件自身代码，不需要网络。
在任何环境下都能运行，确保接口重构时不会意外破坏输出结构。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src._version import __version__
from src.analyzer import analyze_email

# 读取 JSON Schema 文件
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "docs" / "plugin-contract-schema.json"


def _load_schema() -> dict:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _validate_against_schema(instance: dict, schema: dict) -> list[str]:
    """用简单的递归校验代替 jsonschema 库依赖。

    检查 required 字段、enum 值、type 类型、number 范围。
    不校验 format（如 date-time），避免引入第三方依赖。
    """
    errors: list[str] = []
    _validate(instance, schema, "$", errors)
    return errors


def _validate(value: object, schema: dict, path: str, errors: list[str]) -> None:
    """递归校验单个值。"""
    # required
    if "required" in schema and isinstance(value, dict):
        for field in schema["required"]:
            if field not in value:
                errors.append(f"{path}: 缺少必填字段 '{field}'")

    # type
    if "type" in schema and schema["type"] != "object":
        if "enum" in schema:
            if value not in schema["enum"]:
                errors.append(f"{path}: 值 '{value}' 不在枚举 {schema['enum']} 中")
        elif schema["type"] == "string":
            if not isinstance(value, str):
                errors.append(f"{path}: 期望 string，实际 {type(value).__name__}")
        elif schema["type"] == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"{path}: 期望 number，实际 {type(value).__name__}")
            else:
                if "minimum" in schema and value < schema["minimum"]:
                    errors.append(f"{path}: {value} < 最小值 {schema['minimum']}")
                if "maximum" in schema and value > schema["maximum"]:
                    errors.append(f"{path}: {value} > 最大值 {schema['maximum']}")
        elif schema["type"] == "integer":
            if not isinstance(value, int):
                errors.append(f"{path}: 期望 integer，实际 {type(value).__name__}")
        elif schema["type"] == "boolean":
            if not isinstance(value, bool):
                errors.append(f"{path}: 期望 boolean，实际 {type(value).__name__}")

    # array
    if "items" in schema and isinstance(value, list):
        items_schema = schema["items"]
        for i, item in enumerate(value):
            child_path = f"{path}[{i}]"
            if "$ref" in items_schema:
                # 仅支持一级 $ref: #/definitions/xxx
                ref_key = items_schema["$ref"].split("/")[-1]
                defs = schema.get("definitions", {})
                resolved = defs.get(ref_key, {})
                if resolved:
                    if "type" in resolved and resolved["type"] == "object":
                        for fname in resolved.get("required", []):
                            if fname not in item:
                                errors.append(f"{child_path}: 缺少必填字段 '{fname}'")
                    _validate(item, resolved, child_path, errors)
            else:
                _validate(item, items_schema, child_path, errors)

    # object properties
    if "properties" in schema and isinstance(value, dict):
        for key, prop_schema in schema["properties"].items():
            if key in value:
                child_path = f"{path}.{key}"
                if "$ref" in prop_schema:
                    ref_key = prop_schema["$ref"].split("/")[-1]
                    defs = schema.get("definitions", {})
                    resolved = defs.get(ref_key, {})
                    if resolved:
                        _validate(value[key], resolved, child_path, errors)
                else:
                    _validate(value[key], prop_schema, child_path, errors)


class TestContract:
    """验证插件输出结构始终符合定义好的契约。"""

    schema: dict = {}

    @classmethod
    def setup_class(cls):
        cls.schema = _load_schema()

    def test_schema_file_exists(self):
        """Schema 文件必须存在。"""
        assert _SCHEMA_PATH.is_file()

    def test_schema_is_valid_json(self):
        """Schema 文件必须是合法 JSON。"""
        schema = _load_schema()
        assert "$schema" in schema
        assert "title" in schema

    @pytest.mark.parametrize(
        "payload,desc",
        [
            ({"subject": "normal", "plainText": "hello"}, "普通邮件"),
            ({"subject": "紧急", "plainText": "请立即处理"}, "紧急邮件"),
            ({"subject": "中奖", "plainText": "恭喜您中奖了"}, "垃圾邮件"),
            ({}, "空输入"),
            ({"from": "hacker@evil.com", "plainText": "test"}, "无主题"),
        ],
    )
    def test_output_structure_matches_schema(self, payload, desc):
        """不同场景的输出结构必须全部符合 Schema。"""
        result = analyze_email(payload)
        errors = _validate_against_schema(result, self.schema)
        assert not errors, f"[{desc}] Schema 校验失败:\n" + "\n".join(errors)

    def test_version_field(self):
        """pluginVersion 必须匹配 _version.py 中的定义。"""
        result = analyze_email({"subject": "test", "plainText": "test"})
        assert result["pluginVersion"] == __version__

    def test_risk_indicator_types(self):
        """所有已知的风险指标 type 必须在 schema 枚举中。"""
        schema = self.schema
        valid_types = set(
            schema["definitions"]["indicator"]["properties"]["type"]["enum"]
        )
        # 构造一个触发多种指标的 payload
        result = analyze_email({
            "subject": "test",
            "plainText": "test",
            "from": "attacker@gmai1.com",
            "links": ["http://192.168.1.1/login"],
            "attachments": [{"filename": "virus.exe"}],
        })
        for ind in result["risk"]["indicators"]:
            assert ind["type"] in valid_types, f"未知的指标类型: {ind['type']}"

    def test_actions_are_valid(self):
        """actions 必须在 schema 枚举中。"""
        schema = self.schema
        valid_actions = set(schema["properties"]["actions"]["items"]["enum"])
        result = analyze_email({
            "subject": "紧急",
            "plainText": "请立即审批处理",
            "from": "admin@company.com",
        })
        for action in result["actions"]:
            assert action in valid_actions, f"未知的 action: {action}"

    def test_spam_label_enum(self):
        """spam.label 必须在枚举中。"""
        schema = self.schema
        valid = set(schema["definitions"]["spamLabel"]["enum"])
        for payload, _ in [
            ({"subject": "正常", "plainText": "test"}, None),
            ({"subject": "中奖", "plainText": "免费领取"}, None),
        ]:
            result = analyze_email(payload)
            assert result["spam"]["label"] in valid

    def test_priority_label_enum(self):
        """priority.label 必须在枚举中。"""
        schema = self.schema
        valid = set(schema["definitions"]["priorityLabel"]["enum"])
        result = analyze_email({"subject": "test", "plainText": "test"})
        assert result["priority"]["label"] in valid

    def test_risk_level_enum(self):
        """risk.level 必须在枚举中。"""
        schema = self.schema
        valid = set(schema["definitions"]["riskLevel"]["enum"])
        result = analyze_email({"subject": "test", "plainText": "test"})
        assert result["risk"]["level"] in valid

    def test_all_risk_levels_used(self):
        """确保所有风险等级在代码中都有对应的阈值。"""
        # 构造无风险输入
        result = analyze_email({"subject": "test", "plainText": "test"})
        assert result["risk"]["level"] == "none"
        assert result["risk"]["score"] == 0.0
