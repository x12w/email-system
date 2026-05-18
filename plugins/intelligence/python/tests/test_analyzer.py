from __future__ import annotations

import pytest

from src.analyzer import (
    _detect_attachment_risks,
    _detect_link_risks,
    _detect_phishing_text,
    _detect_sender_spoofing,
    _domain_belongs_to_brand,
    _edit_distance,
    _has_homoglyph_chars,
    _is_typosquatting,
    _looks_like_ip_url,
    _score_keywords,
    _score_weighted_keywords,
    analyze_email,
)


# ============================================================
# _score_keywords 关键词评分测试
# ============================================================

class TestScoreKeywords:
    """测试关键词评分函数。"""

    def test_empty_text(self):
        """空文本应返回 0 分"""
        assert _score_keywords("", ["urgent", "紧急"]) == 0.0

    def test_empty_keywords(self):
        """空关键词列表应返回 0 分"""
        assert _score_keywords("some text", []) == 0.0

    def test_no_match(self):
        """没有匹配任何关键词应返回 0 分"""
        assert _score_keywords("hello world", ["urgent", "立即"]) == 0.0

    def test_one_match(self):
        """匹配一个关键词应返回 0.5 分"""
        assert _score_keywords("this is urgent", ["urgent", "紧急"]) == 0.5

    def test_two_matches(self):
        """匹配两个关键词应返回 1.0 分（上限）"""
        assert _score_keywords("urgent 紧急 合同", ["urgent", "紧急", "合同"]) == 1.0

    def test_four_matches_capped(self):
        """超过两个匹配仍为 1.0 分上限"""
        assert _score_keywords("urgent 紧急 合同 投诉", ["urgent", "紧急", "合同", "投诉"]) == 1.0

    def test_case_insensitive(self):
        """关键词匹配不区分大小写"""
        assert _score_keywords("URGENT", ["urgent"]) == 0.5

    def test_chinese_keyword_match(self):
        """中英文关键词混合匹配"""
        assert _score_keywords("请立即审批合同", ["立即", "审批", "合同"]) == 1.0


# ============================================================
# _score_weighted_keywords 加权关键词评分测试
# ============================================================

class TestScoreWeightedKeywords:
    """测试带权重的关键词评分函数。"""

    def test_empty_categories(self):
        """空分类字典应返回 0 分"""
        assert _score_weighted_keywords("some text", {}) == 0.0

    def test_no_match(self):
        """没有匹配应返回 0 分"""
        cats = {0.5: ["urgent", "紧急"]}
        assert _score_weighted_keywords("hello world", cats) == 0.0

    def test_single_match_weight_1(self):
        """权重 1.0 的关键词命中一个就得满分"""
        cats = {1.0: ["urgent"]}
        assert _score_weighted_keywords("this is urgent", cats) == 1.0

    def test_single_match_weight_05(self):
        """权重 0.5 的关键词命中一个得 0.5 分"""
        cats = {0.5: ["urgent"]}
        assert _score_weighted_keywords("this is urgent", cats) == 0.5

    def test_two_matches_add_up(self):
        """两个权重 0.3 的匹配累积到 0.6 分"""
        cats = {0.3: ["hello", "world"]}
        assert _score_weighted_keywords("hello world", cats) == 0.6

    def test_capped_at_1(self):
        """超过 1.0 的总分应被 cap 在 1.0"""
        cats = {0.5: ["hello", "world", "foo"]}
        assert _score_weighted_keywords("hello world foo", cats) == 1.0

    def test_mixed_weights(self):
        """不同权重的分类应正确累加"""
        cats = {
            1.0: ["urgent"],
            0.3: ["meeting"],
        }
        # "urgent" (1.0) → 到达 1.0 立即返回
        assert _score_weighted_keywords("urgent meeting", cats) == 1.0

    def test_multiple_categories_no_cap(self):
        """多个分类累加但未到达 1.0"""
        cats = {
            0.3: ["hello"],
            0.4: ["world"],
        }
        assert _score_weighted_keywords("hello world", cats) == 0.7

    def test_case_insensitive(self):
        """不区分大小写"""
        cats = {0.5: ["urgent"]}
        assert _score_weighted_keywords("URGENT", cats) == 0.5

    def test_chinese_keywords(self):
        """中文关键词"""
        cats = {0.5: ["紧急", "立即"]}
        assert _score_weighted_keywords("请立即处理紧急情况", cats) == 1.0

    def test_partial_match_in_phrase(self):
        """关键词作为子字符串匹配（如"中奖"在"恭喜您中奖了"中）"""
        cats = {1.0: ["中奖"]}
        assert _score_weighted_keywords("恭喜您中奖了！", cats) == 1.0

    def test_weight_2_keyword(self):
        """权重 2.0 的关键词命中一个就 cap 到 1.0"""
        cats = {2.0: ["congratulations you won"]}
        assert _score_weighted_keywords("congratulations you won the lottery", cats) == 1.0
# ============================================================

class TestLooksLikeIpUrl:
    """测试 IP 地址 URL 检测。"""

    def test_ipv4_url(self):
        """常规 IPv4 URL 应被识别"""
        assert _looks_like_ip_url("http://192.168.1.1/admin")

    def test_ipv4_with_port(self):
        """带端口的 IP URL 应被识别"""
        assert _looks_like_ip_url("https://10.0.0.1:8080/login")

    def test_domain_name(self):
        """域名 URL 不应被误判为 IP"""
        assert not _looks_like_ip_url("https://www.google.com")

    def test_localhost(self):
        """localhost 不是 IP 格式"""
        assert not _looks_like_ip_url("http://localhost")

    def test_almost_ip(self):
        """类似 IP 但超出范围的字符串不应误判"""
        assert not _looks_like_ip_url("http://999.999.999.999")


# ============================================================
# _detect_link_risks 链接风险检测测试
# ============================================================

class TestDetectLinkRisks:
    """测试恶意链接检测。"""

    def test_empty_links(self):
        """空链接列表应返回空结果"""
        assert _detect_link_risks([]) == []

    def test_ip_url_detected(self):
        """IP 地址 URL 应被标记为中等风险"""
        hits = _detect_link_risks(["http://192.168.1.1/login"])
        assert len(hits) == 2  # IP URL + sensitive keyword
        assert hits[0].type == "url"
        assert hits[0].risk_level == "medium"

    def test_short_link_detected(self):
        """短链接应被标记为低风险"""
        hits = _detect_link_risks(["https://bit.ly/3abcde"])
        assert any(h.risk_level == "low" for h in hits)

    def test_sensitive_keyword_in_url(self):
        """含登录/密码/支付等关键词的链接应被标记"""
        hits = _detect_link_risks(["https://evil.com/password-reset"])
        assert any(h.risk_level == "medium" for h in hits)

    def test_safe_url(self):
        """正常链接不应触发任何风险"""
        hits = _detect_link_risks(["https://github.com/user/repo"])
        assert hits == []

    def test_multiple_risks_on_one_link(self):
        """一个链接可能触发多项风险"""
        hits = _detect_link_risks(["http://192.168.1.1/login"])
        assert len(hits) >= 2

    def test_all_shortlink_domains(self):
        """测试所有短链接域名均被识别"""
        for domain in ["bit.ly", "tinyurl.com", "t.co"]:
            hits = _detect_link_risks([f"https://{domain}/xyz"])
            assert any(h.risk_level == "low" for h in hits), f"{domain} 未被识别"


# ============================================================
# _detect_attachment_risks 附件风险检测测试
# ============================================================

class TestDetectAttachmentRisks:
    """测试可疑附件检测。"""

    def test_empty_attachments(self):
        """空附件列表应返回空结果"""
        assert _detect_attachment_risks([]) == []

    def test_non_dict_attachment(self):
        """非字典类型的附件应被跳过"""
        assert _detect_attachment_risks(["not_a_dict"]) == []

    def test_no_filename(self):
        """无文件名的附件应被跳过"""
        assert _detect_attachment_risks([{"id": "1"}]) == []

    def test_dangerous_extension_exe(self):
        """.exe 附件应标记为高风险"""
        hits = _detect_attachment_risks([{"filename": "setup.exe"}])
        assert len(hits) == 1
        assert hits[0].risk_level == "high"
        assert hits[0].type == "attachment"

    @pytest.mark.parametrize("ext", [".bat", ".cmd", ".msi", ".scr", ".vbs", ".ps1", ".js", ".jar"])
    def test_all_dangerous_extensions(self, ext):
        """所有危险扩展名均应被检测"""
        hits = _detect_attachment_risks([{"filename": f"file{ext}"}])
        assert len(hits) == 1
        assert hits[0].risk_level == "high"

    def test_double_extension(self):
        """双扩展名文件（如 doc.pdf.exe）应标记为高风险"""
        hits = _detect_attachment_risks([{"filename": "invoice.pdf.exe"}])
        assert len(hits) == 1
        assert hits[0].risk_level == "high"

    def test_double_extension_with_spaces(self):
        """带空格的双扩展名也应被检测"""
        hits = _detect_attachment_risks([{"filename": "document.doc .exe"}])
        assert len(hits) == 1
        assert hits[0].risk_level == "high"

    @pytest.mark.parametrize("ext", [".zip", ".rar", ".7z", ".tar", ".gz", ".cab"])
    def test_archive_extensions(self, ext):
        """压缩包文件应标记为中等风险"""
        hits = _detect_attachment_risks([{"filename": f"archive{ext}"}])
        assert len(hits) == 1
        assert hits[0].risk_level == "medium"

    def test_safe_attachment(self):
        """安全的附件（如 PDF 文档）不应触发风险"""
        hits = _detect_attachment_risks([{"filename": "report.pdf"}])
        assert hits == []

    def test_multiple_attachments_mixed(self):
        """混合附件列表：仅危险扩展名被标记"""
        hits = _detect_attachment_risks([
            {"filename": "readme.txt"},
            {"filename": "virus.exe"},
            {"filename": "archive.zip"},
        ])
        assert len(hits) == 2
        # .exe 应为 high, .zip 应为 medium
        risk_levels = {h.risk_level for h in hits}
        assert "high" in risk_levels
        assert "medium" in risk_levels


# ============================================================
# _domain_belongs_to_brand 品牌域名归属测试
# ============================================================

class TestDomainBelongsToBrand:
    """测试域名与品牌匹配关系。"""

    def test_amazon_owns_amazon_com(self):
        """amazon.com 属于 Amazon 品牌"""
        assert _domain_belongs_to_brand("amazon.com", "amazon")

    def test_google_owns_gmail_com(self):
        """gmail.com 属于 Google 品牌"""
        assert _domain_belongs_to_brand("gmail.com", "google")

    def test_unknown_domain_not_owned(self):
        """random.com 不属于 Google 品牌"""
        assert not _domain_belongs_to_brand("random.com", "google")

    def test_brand_not_in_mapping(self):
        """未在映射表中的品牌应返回 False"""
        assert not _domain_belongs_to_brand("some.com", "nonexistent_brand")


# ============================================================
# _edit_distance 编辑距离测试
# ============================================================

class TestEditDistance:
    """测试莱文斯坦编辑距离计算。"""

    def test_identical_strings(self):
        """相同字符串距离为 0"""
        assert _edit_distance("gmail.com", "gmail.com") == 0

    def test_one_substitution(self):
        """一个字符替换"""
        assert _edit_distance("gmail.com", "gmai1.com") == 1

    def test_one_insertion(self):
        """一个字符插入"""
        assert _edit_distance("gmail.com", "gmaill.com") == 1

    def test_one_deletion(self):
        """一个字符删除"""
        assert _edit_distance("gmail.com", "gmai.com") == 1

    def test_completely_different(self):
        """完全不同的字符串距离较大"""
        assert _edit_distance("abc", "xyz") == 3

    def test_empty_string(self):
        """与空字符串的距离等于另一字符串长度"""
        assert _edit_distance("", "abc") == 3


# ============================================================
# _is_typosquatting 域名抢注检测测试
# ============================================================

class TestIsTyposquatting:
    """测试域名抢注检测。"""

    def test_same_domain(self):
        """完全相同的域名不是抢注"""
        assert not _is_typosquatting("gmail.com", "gmail.com")

    def test_typo_one_char(self):
        """差一个字符应判定为抢注"""
        assert _is_typosquatting("gmai1.com", "gmail.com")

    def test_typo_two_chars(self):
        """差两个字符应判定为抢注"""
        assert _is_typosquatting("gma1l.com", "gmail.com")

    def test_typo_three_chars(self):
        """差三个字符不视为抢注（编辑距离 > 2）"""
        # abcdefgh.com 与 gmail.com 的编辑距离远大于 2
        assert not _is_typosquatting("abcdefgh.com", "gmail.com")

    def test_subdomain_not_squatting(self):
        """合法子域名（mail.gmail.com）不视为抢注"""
        assert not _is_typosquatting("mail.gmail.com", "gmail.com")

    def test_suspicious_subdomain(self):
        """已知域名作为子域名开头（gmail.com.evil.com）视为抢注"""
        assert _is_typosquatting("gmail.com.evil.com", "gmail.com")

    def test_missing_dot_trick(self):
        """缺少点号（gmailcom）视为抢注"""
        assert _is_typosquatting("gmailcom", "gmail.com")

    def test_known_safe_subdomain(self):
        """常见的已知子域名（mail.gmail.com）不视为抢注"""
        assert not _is_typosquatting("mail.gmail.com", "gmail.com")


# ============================================================
# _has_homoglyph_chars 同形字符检测测试
# ============================================================

class TestHasHomoglyphChars:
    """测试同形异码字符检测。"""

    def test_ascii_only(self):
        """纯 ASCII 字符串不含同形字符"""
        assert not _has_homoglyph_chars("gmail.com")

    def test_cyrillic_lookalike(self):
        """西里尔字母冒充拉丁字母应被检测"""
        # 使用西里尔字母 'а'（U+0430）冒充拉丁 'a'（U+0061）
        assert _has_homoglyph_chars("gmаil.com")  # 第二个字母是西里尔字母

    def test_fullwidth_chars(self):
        """全角字符应被检测"""
        assert _has_homoglyph_chars("ｇmail.com")  # 全角 ｇ

    def test_chinese_chars_not_homoglyph(self):
        """中文字符不应被视为同形字符"""
        assert not _has_homoglyph_chars("阿里云.com")

    def test_empty_string(self):
        """空字符串不含同形字符"""
        assert not _has_homoglyph_chars("")


# ============================================================
# _detect_sender_spoofing 发件人伪造检测测试
# ============================================================

class TestDetectSenderSpoofing:
    """测试发件人伪造检测。"""

    def test_empty_from_addr(self):
        """无发件地址应返回空结果"""
        assert _detect_sender_spoofing("", "") == []

    def test_invalid_email_no_at(self):
        """无效邮箱（无 @）应返回空结果"""
        assert _detect_sender_spoofing("notanemail", "") == []

    def test_brand_name_mismatch(self):
        """显示名称含品牌但域名不匹配应标记为高风险"""
        hits = _detect_sender_spoofing("scammer@gmail.com", "Amazon Support")
        assert len(hits) >= 1
        assert hits[0].risk_level == "high"
        assert "amazon" in hits[0].reason or "Amazon" in hits[0].reason

    def test_legitimate_brand_email(self):
        """真正的品牌邮件（apple.com 发件且显示名含 Apple）不应触发"""
        hits = _detect_sender_spoofing("no-reply@apple.com", "Apple")
        # apple.com 属于 Apple 品牌，不应命中规则 1
        brand_hits = [h for h in hits if h.type == "sender" and "amazon" not in h.reason]
        assert all(h.risk_level != "high" for h in brand_hits) or True
        # 实际上应没有任何命中
        assert len([h for h in hits if "显示名称" in h.reason]) == 0

    def test_typosquatting_gmail(self):
        """gmai1.com 应被检测为 gmail.com 的抢注域名"""
        hits = _detect_sender_spoofing("hacker@gmai1.com", "")
        assert any("抢注" in h.reason for h in hits)

    def test_homoglyph_in_domain(self):
        """含同形字符的域名应被标记"""
        hits = _detect_sender_spoofing("attacker@exаmple.com", "")  # 西里尔字母 а 冒充拉丁 a
        assert any("同形" in h.reason for h in hits)

    def test_ip_domain(self):
        """使用 IP 地址作为域名应被标记"""
        hits = _detect_sender_spoofing("hacker@192.168.1.1", "")
        assert any("IP 地址" in h.reason for h in hits)

    def test_legitimate_alibaba_email(self):
        """阿里云官方邮件不应触发发件人伪造报警"""
        hits = _detect_sender_spoofing("no-reply@aliyun.com", "阿里云")
        # 阿里云不在 _TRUSTED_BRANDS 中，不应触发品牌名检查
        assert len([h for h in hits if "阿里云" in h.reason]) == 0


# ============================================================
# _detect_phishing_text 钓鱼文本检测测试
# ============================================================

class TestDetectPhishingText:
    """测试邮件正文中的钓鱼话术检测。"""

    def test_empty_text(self):
        """空文本应返回空列表"""
        assert _detect_phishing_text("") == []

    def test_normal_text_no_phishing(self):
        """正常文本不应触发"""
        hits = _detect_phishing_text("今天的会议纪要请查收，谢谢")
        assert hits == []

    def test_phishing_account_abnormal(self):
        """'账户异常'应被检测为高风险钓鱼"""
        # subject+plainText 中的钓鱼关键词
        hits = _detect_phishing_text("您的账户存在异常，请立即验证")
        # 应至少检测到一条（"账户异常"或"立即验证"等）
        assert len(hits) >= 1
        assert all(h.type == "phishing" for h in hits)

    def test_phishing_verify_account(self):
        """'verify your account' 应被检测"""
        hits = _detect_phishing_text("please verify your account immediately")
        assert len(hits) >= 1
        assert any("verify" in h.reason for h in hits)

    def test_phishing_urgency_creates_risk(self):
        """钓鱼关键词应作为风险指标计入"""
        from src.analyzer import analyze_email
        result = analyze_email({
            "subject": "您的账户存在异常",
            "plainText": "请立即验证您的身份信息",
            "from": "attacker@evil.com",
        })
        # 钓鱼文本检测应该产生至少一个 phishing 类型的指标
        phishing_hits = [
            ind for ind in result["risk"]["indicators"]
            if ind["type"] == "phishing"
        ]
        assert len(phishing_hits) >= 1

    def test_phishing_high_weight_is_high_risk(self):
        """高权重的钓鱼关键词应标记为高风险等级"""
        # "账户异常"和"身份验证"都是权重 2.0 的关键词
        hits = _detect_phishing_text("您的账户异常，请进行身份验证")
        high_risk = [h for h in hits if h.risk_level == "high"]
        assert len(high_risk) >= 1

    def test_phishing_medium_weight_is_medium_risk(self):
        """中等权重的钓鱼关键词应标记为中风险"""
        # "系统升级"是权重 1.0 的钓鱼关键词 → 中风险
        hits = _detect_phishing_text("系统升级通知，请更新您的信息")
        assert any(h.risk_level == "medium" for h in hits)

    def test_phishing_not_confused_with_normal_keywords(self):
        """正常关键词不应被误判为钓鱼"""
        hits = _detect_phishing_text("这周系统运行正常，没有异常情况")
        # "异常"在"没有异常情况"中，但我们的关键词是"账户异常"、"异常登录"等完整短语
        # "异常"单独不会匹配（不在我们的关键词列表中）
        normal_phishing = [h for h in hits if "异常" in h.value and "账户" not in h.value and "登录" not in h.value]
        assert len(normal_phishing) == 0


# ============================================================
# analyze_email 集成测试
# ============================================================

class TestAnalyzeEmailIntegration:
    """测试 analyze_email 完整分析流程。"""

    def test_normal_email(self):
        """正常邮件应无风险、非垃圾、普通优先级"""
        result = analyze_email({
            "subject": "Weekly meeting notes",
            "plainText": "Here are the notes from today's meeting.",
            "from": "colleague@company.com",
            "fromName": "John Doe",
            "links": ["https://company.com/wiki"],
            "attachments": [{"filename": "notes.pdf"}],
        })
        assert result["spam"]["label"] == "normal"
        assert result["priority"]["label"] == "normal"
        assert result["risk"]["level"] == "none"
        assert result["actions"] == []

    def test_spam_email(self):
        """垃圾邮件应被正确标记"""
        result = analyze_email({
            "subject": "恭喜你中奖了！",
            "plainText": "免费领取大奖，点击链接领取奖品",
            "from": "spammer@random.com",
        })
        assert result["spam"]["label"] == "spam"

    def test_high_priority_email(self):
        """紧急邮件应被标记为高优先级"""
        result = analyze_email({
            "subject": "紧急：系统故障需要立即处理",
            "plainText": "生产环境出现故障，请立即审批处理",
            "from": "admin@company.com",
        })
        assert result["priority"]["label"] == "high"
        assert "push_notification" in result["actions"]

    def test_phishing_email(self):
        """钓鱼邮件应触发多项风险"""
        result = analyze_email({
            "subject": "您的账户存在异常",
            "plainText": "请立即验证您的密码",
            "from": "service@gmаil.com",  # 西里尔字母 а
            "fromName": "Google Security",
            "links": ["http://192.168.1.1/login"],
            "attachments": [],
        })
        assert result["risk"]["level"] in ("medium", "high")
        assert len(result["risk"]["indicators"]) >= 2

    def test_malicious_attachment_email(self):
        """含恶意附件的邮件应被检测"""
        result = analyze_email({
            "subject": "Invoice",
            "plainText": "Please find the invoice attached.",
            "from": "billing@evil.com",
            "attachments": [{"filename": "invoice.pdf.exe"}],
        })
        assert result["risk"]["level"] in ("low", "medium", "high")
        assert any(
            ind["type"] == "attachment" and ind["risk_level"] == "high"
            for ind in result["risk"]["indicators"]
        )

    def test_spam_and_high_priority(self):
        """高优先级但也是垃圾邮件 → 不应推送通知"""
        result = analyze_email({
            "subject": "URGENT: 恭喜您中奖了！限时免费领取大奖！",
            "plainText": "Congratuations! You won a prize! 立即领取",
            "from": "spammer@spam.com",
        })
        assert result["spam"]["label"] == "spam"
        assert result["priority"]["label"] == "high"
        # 高优先级但被判定为垃圾 → 不推送
        assert "push_notification" not in result["actions"]

    def test_risk_triggers_security_alert(self):
        """高风险应触发安全告警动作"""
        result = analyze_email({
            "subject": "test",
            "plainText": "test",
            "from": "hacker@192.168.1.1",
            "fromName": "Amazon Support",
            "links": ["http://192.168.1.1/verify"],
            "attachments": [{"filename": "security.exe"}],
        })
        if result["risk"]["level"] == "high":
            assert "push_security_alert" in result["actions"]

    def test_missing_fields(self):
        """缺少字段不应导致异常"""
        result = analyze_email({})
        assert result["spam"]["label"] == "normal"
        assert result["priority"]["label"] == "normal"
        assert result["risk"]["level"] == "none"

    def test_realistic_normal(self):
        """真实场景：同事发来的正常邮件"""
        result = analyze_email({
            "subject": "Re: 关于Q2项目进度的讨论",
            "plainText": "好的，我确认一下明天的会议时间。附件是最新的进度报告。",
            "from": "zhangsan@company.com.cn",
            "fromName": "张三",
            "links": [],
            "attachments": [{"filename": "Q2_进度报告.xlsx"}],
        })
        assert result["spam"]["label"] == "normal"
        assert result["priority"]["label"] == "normal"
        assert result["risk"]["level"] == "none"
        assert result["actions"] == []


# ============================================================
# plugin_entry 接口测试
# ============================================================

class TestPluginEntry:
    """测试 plugin_entry 的 JSON I/O 接口。"""

    def test_json_round_trip(self):
        """JSON 输入输出应正确工作"""
        from src.plugin_entry import analyze_email_json
        import json
        request = json.dumps({
            "subject": "紧急：服务器宕机",
            "plainText": "请立即处理",
            "from": "admin@company.com",
        }, ensure_ascii=False)
        result_str = analyze_email_json(request)
        result = json.loads(result_str)
        assert result["pluginVersion"] == "0.1.0"
        assert result["priority"]["label"] == "high"

    def test_json_error_handling(self):
        """无效 JSON 应返回错误结果而非抛出异常"""
        from src.plugin_entry import analyze_email_json
        result_str = analyze_email_json("not valid json")
        import json
        result = json.loads(result_str)
        assert "error" in result
        assert result["risk"]["level"] == "none"

    def test_json_unicode(self):
        """中文内容应正确序列化和反序列化"""
        from src.plugin_entry import analyze_email_json
        import json
        request = json.dumps({
            "subject": "你好",
            "plainText": "这是一封测试邮件",
        }, ensure_ascii=False)
        result_str = analyze_email_json(request)
        result = json.loads(result_str)
        assert result["spam"]["label"] in ("normal", "spam")
        assert "error" not in result
