from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# 从 keywords.py 加载关键词词库（数据存放在 data/ 目录下的 JSON 文件中）
# 这样 analyzer.py 只负责分析逻辑，不会被大量关键词数据撑满
from ._version import __version__
from .config import DEFAULT_CONFIG, PluginConfig
from .keywords import _HIGH_PRIORITY_KEYWORDS, _SPAM_KEYWORDS, _PHISHING_KEYWORDS


# @dataclass 是 Python 的一个装饰器，能自动帮我们生成 __init__
# （构造函数）、__repr__（打印字符串）等方法，省去手写的麻烦。
# frozen=True 表示这个类的实例一旦创建就不能修改（不可变对象），
# 这样可以避免代码里不小心改了检测结果。
@dataclass(frozen=True)
class RuleHit:
    """表示一条风险检测结果的"记录"。

    比如检测到一个链接是恶意链接，就会创建一个 RuleHit 对象，
    记录下这个结果的相关信息。

    Attributes:
        type:      风险类型，比如 "url"（链接）、"attachment"（附件）、"sender"（发件人）
        value:     触发风险的具体内容，比如具体的链接地址
        risk_level:风险等级，"low" / "medium" / "high"
        reason:    为什么判定为风险，用中文描述
    """
    type: str
    value: str
    risk_level: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """把 RuleHit 转成字段名符合接口规范的字典。

        接口文档要求使用 camelCase（驼峰命名），比如 riskLevel，
        但 Python 中习惯用 snake_case（下划线命名）。
        这个方法在序列化时做一次映射转换。

        Returns:
            {
                "type":     风险类型
                "value":    风险内容
                "riskLevel": 风险等级（注意是大写 L，不是下划线）
                "reason":   风险原因
            }
        """
        return {
            "type": self.type,
            "value": self.value,
            "riskLevel": self.risk_level,
            "reason": self.reason,
        }


# frozenset 和 set 类似，都是"集合"，但 frozenset 是不可变的。
# 不可变的好处：可以作为常量使用，不会被意外修改，而且可以放进另一个集合里。
# 这里用 frozenset 是因为这些品牌列表是固定的数据，不应该被修改。
_TRUSTED_BRANDS = frozenset({
    # ---------- 国际品牌 ----------
    "amazon", "aws", "apple", "google", "microsoft", "office 365",
    "paypal", "alipay",
    "tencent",
    "bank",  # 泛指银行类
    "dhl", "fedex",
    "netflix", "spotify", "facebook", "meta", "linkedin",
    "github", "gitlab", "atlassian", "slack", "zoom",
    "adobe", "oracle", "ibm",
    # ---------- 国内品牌/中文名 ----------
    "支付宝", "微信", "腾讯",
    "顺丰速运", "中国邮政",
    "银行", "工商银行", "建设银行", "农业银行",
    "中国银行", "招商银行",
    "顺丰",
    "华为", "huawei", "小米",
})

# 常见的合法邮箱域名列表。
# 在检测"域名抢注"时需要它们作为对照，看发件人域名是不是冒充这些域名。
_KNOWN_DOMAINS = frozenset({
    # 国际邮箱
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
    # 国内邮箱
    "163.com", "126.com", "qq.com", "foxmail.com", "sina.com",
    "sohu.com", "aliyun.com",
    # 其他
    "icloud.com", "proton.me",
})

# 危险附件扩展名：这些是可执行文件或脚本文件。
# 攻击者经常把这类文件作为邮件附件发送，收件人一旦打开，电脑就可能中毒。
_DANGEROUS_EXTENSIONS = frozenset({
    # Windows 可执行文件
    ".exe", ".bat", ".cmd", ".msi", ".scr", ".com",
    # 动态链接库（可被注入）
    ".dll",
    # 脚本文件（可被系统执行）
    ".vbs", ".ps1", ".js", ".jar", ".wsf",
    ".vbe", ".pif", ".gadget", ".msc",
    # 注册表文件（修改注册表可能导致安全问题）
    ".reg",
})

# 压缩包扩展名：压缩包本身不危险，但里面可能藏着恶意文件。
_ARCHIVE_EXTENSIONS = frozenset({".zip", ".rar", ".7z", ".tar", ".gz", ".cab"})

# 双扩展名模式的正则表达式。
# re.compile 会把正则表达式"编译"成一个对象，反复使用时速度更快。
# 这个模式要匹配的是像 "invoice.doc.pdf.exe" 这样的文件名——
# 攻击者用多层扩展名来伪装文件，让收件人以为是个安全文档，实际上是可执行文件。
_DOUBLE_EXT_PATTERN = re.compile(
    # 第一层：看起来安全的扩展名（文档、图片、媒体文件等）
    r"\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|jpg|jpeg|png|gif|mp3|mp4)"
    # 中间可能有空格
    r"\s*"
    # 第二层：实际的可执行扩展名（这才是真实的文件类型）
    r"\.(exe|bat|cmd|msi|scr|vbs|ps1|js|jar|com)",
    re.IGNORECASE  # 忽略大小写，.EXE 和 .exe 都匹配
)


def analyze_email(payload: dict[str, Any], config: PluginConfig | None = None) -> dict[str, Any]:
    """这是整个插件的核心函数，对一封邮件进行全面的安全分析。

    分析四个方面：
    1. 是否为垃圾邮件（spam）
    2. 是否为高优先级邮件（含紧急关键词等）
    3. 是否存在安全风险（恶意链接、可疑附件、发件人伪造、HTML 隐藏内容）
    4. 根据分析结果，决定需要采取什么行动（如推送通知、安全警报）

    字段名遵循接口文档约定：
    - 输入：messageId、from、to、subject、plainText、html、links、attachments、locale
    - 输出：spam.label、priority.label、risk.level、risk.indicators[].riskLevel

    Args:
        payload: 传入的邮件数据字典
        config:  可选的自定义配置，为 None 时使用 DEFAULT_CONFIG

    Returns:
        分析结果字典
    """
    # ========== 提取输入字段 ==========
    request_id = payload.get("requestId") or ""
    message_id = payload.get("messageId") or 0
    subject = str(payload.get("subject") or "")
    plain_text = str(payload.get("plainText") or "")
    html_content = str(payload.get("html") or "")
    links = payload.get("links") or []
    attachments = payload.get("attachments") or []
    from_addr = str(payload.get("from") or "")
    from_name = str(payload.get("fromName") or "")
    to_addrs = payload.get("to") or []
    locale = str(payload.get("locale") or "")

    # 使用配置，未传入时使用默认配置
    if config is None:
        config = DEFAULT_CONFIG

    # 把邮件主题和正文拼接在一起转小写，方便统一做关键词匹配
    # 如果有 HTML 内容，也一并提取纯文本后加入分析
    combined_text = subject
    if plain_text:
        combined_text += "\n" + plain_text
    if html_content:
        # 简单去除 HTML 标签，提取可见文本
        plain_from_html = re.sub(r"<[^>]+>", " ", html_content)
        plain_from_html = re.sub(r"\s+", " ", plain_from_html).strip()
        combined_text += "\n" + plain_from_html
    text = combined_text.lower()

    # ========== 关键词评分 ==========
    high_priority_score = _score_weighted_keywords(text, _HIGH_PRIORITY_KEYWORDS)
    spam_score = _score_weighted_keywords(text, _SPAM_KEYWORDS)

    # ========== 风险检测 ==========
    # 每个检测器受 config 中的功能开关控制
    indicators: list[RuleHit] = []
    if config.enable_link_detection:
        indicators.extend(_detect_link_risks(links))
    if config.enable_attachment_detection:
        indicators.extend(_detect_attachment_risks(attachments))
    if config.enable_sender_detection:
        indicators.extend(_detect_sender_spoofing(from_addr, from_name))
    if config.enable_phishing_detection:
        indicators.extend(_detect_phishing_text(text))
    if config.enable_html_analysis:
        indicators.extend(_detect_html_risks(html_content))

    # ========== 风险评分 ==========
    # 风险等级遵循接口文档 5 级定义：none / low / medium / high / critical
    risk_score = min(1.0, config.risk_indicator_weight * len(indicators))
    if risk_score >= 0.9:
        risk_level = "critical"
    elif risk_score >= 0.75:
        risk_level = "high"
    elif risk_score >= 0.5:
        risk_level = "medium"
    elif risk_score > 0:
        risk_level = "low"
    else:
        risk_level = "none"

    # ========== 标签判定 ==========
    # 优先级标签：文档要求 three levels — low / normal / high
    if high_priority_score >= config.priority_threshold:
        priority_label = "high"
        # 根据分数高低给出具体的理由说明
        if high_priority_score >= 0.8:
            priority_reasons = ["邮件包含紧急关键词，建议立即查看"]
        else:
            priority_reasons = ["邮件包含重要关键词，需要关注"]
    elif high_priority_score >= 0.1:
        priority_label = "normal"
        priority_reasons = []
    else:
        priority_label = "low"
        priority_reasons = []

    # 垃圾邮件标签
    spam_label = "spam" if spam_score >= config.spam_threshold else "normal"

    # ========== 行动决策 ==========
    actions: list[str] = []
    if priority_label == "high" and spam_label != "spam":
        actions.append("mark_high_priority")
        actions.append("push_notification")
    if risk_level in {"high", "critical"}:
        actions.append("push_security_alert")

    # ========== 构建返回结果 ==========
    result: dict[str, Any] = {
        "pluginVersion": __version__,
        "analyzedAt": datetime.now(timezone.utc).isoformat(),
        "spam": {"label": spam_label, "score": spam_score},
        "priority": {
            "label": priority_label,
            "score": high_priority_score,
            "reasons": priority_reasons,
        },
        "risk": {
            "level": risk_level,
            "score": risk_score,
            "indicators": [hit.to_dict() for hit in indicators],
        },
        "actions": actions,
    }

    # 原样回传 requestId 和 messageId，方便 Java 后端做请求追踪
    if request_id:
        result["requestId"] = request_id
    if message_id:
        result["messageId"] = message_id

    return result


def _score_keywords(text: str, keywords: list[str]) -> float:
    """在文本中查找关键词，根据命中的关键词数量计算得分。

    这个函数的工作方式：
    1. 把文本转成小写（方便不区分大小写匹配）
    2. 遍历关键词列表，每个关键词如果在文本中出现就算一次"命中"
    3. 每命中一个关键词加 0.5 分，最高 1.0 分

    例如：文本 "紧急通知：您的账号需要立即验证"
        匹配关键词 ["紧急", "立即"] → 命中了 2 个 → 得分 = min(1.0, 2/2) = 1.0

    Args:
        text:     要搜索的文本（已转小写）
        keywords: 要查找的关键词列表

    Returns:
        0.0 ~ 1.0 之间的浮点数。每命中一个关键词加 0.5，最多 1.0。
    """
    if not keywords:
        return 0.0
    # 把文本转小写，这样匹配时不区分大小写
    # 比如 "Urgent" 能匹配到关键词 "urgent"
    text_lower = text.lower()
    # 用列表推导式统计命中了多少个关键词
    # keyword.lower() in text_lower 的意思是：这个关键词是否出现在文本中
    hits = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    # 每命中一个得 0.5 分，但不超过 1.0
    return min(1.0, hits / 2)


def _score_weighted_keywords(text: str, categories: dict[float, list[str]]) -> float:
    """使用带权重的分类词库计算文本得分。

    这是 _score_keywords 的升级版。不同之处：
    - _score_keywords：所有关键词权重相同（每个 0.5 分）
    - _score_weighted_keywords：不同分类的关键词有不同权重

    权重越高，说明这个词是垃圾/紧急信号的可信度越高。
    比如"中奖"(权重 1.0)比"优惠"(权重 0.5)更可能是垃圾邮件。

    工作原理：
    1. 遍历 categories 字典中的每个 (权重, 关键词列表) 分组
    2. 检查每个关键词是否出现在文本中
    3. 如果命中，总分加上对应的权重
    4. 一旦总分达到 1.0，立即返回（提前退出，提高效率）

    Args:
        text:       要搜索的文本
        categories: 字典，格式 {权重值: [关键词列表], ...}
                    例如：{1.0: ["urgent", "紧急"], 0.5: ["审批", "invoice"]}

    Returns:
        0.0 ~ 1.0 之间的浮点数
    """
    if not categories:
        return 0.0
    text_lower = text.lower()
    score = 0.0

    # 遍历每个权重分组
    # items() 返回字典的 (键, 值) 对
    for weight, keywords in categories.items():
        for keyword in keywords:
            # 检查关键词是否出现在文本中
            if keyword.lower() in text_lower:
                score += weight
                # 一旦达到或超过 1.0 就提前结束
                # 因为最终结果会被 cap 到 1.0，没必要继续算了
                if score >= 1.0:
                    return 1.0

    # 用 min(1.0, score) 确保不超过 1.0
    return min(1.0, score)


def _detect_link_risks(links: list[Any]) -> list[RuleHit]:
    """检测邮件中的链接是否存在风险。

    三种检测：
    1. IP 地址 URL：链接的主机名直接是 IP 地址（如 http://192.168.1.1/login），
       正规网站一般用域名而不是 IP
    2. 短链接：像 bit.ly 这类短链接服务可以被攻击者用来隐藏真实地址
    3. 链接含敏感关键词：链接中含有 login/password/pay 等词，
       可能是钓鱼链接（伪装成登录页面骗取密码）

    Args:
        links: 链接字符串列表

    Returns:
        检测到的风险指标列表（每个指标是一个 RuleHit 对象）
    """
    hits: list[RuleHit] = []
    for raw_link in links:
        link = str(raw_link)
        lowered = link.lower()

        # 检查 1：如果链接是 http:// 或 https:// 开头，且主机名是 IP 地址
        if "://" in lowered and _looks_like_ip_url(lowered):
            hits.append(RuleHit("url", link, "medium", "链接使用 IP 地址作为主机名"))

        # 检查 2：如果是短链接（用 in 判断是否包含这些短链接域名）
        if any(domain in lowered for domain in ["bit.ly", "tinyurl.com", "t.co"]):
            hits.append(RuleHit("url", link, "low", "短链接需要点击展开，存在重定向风险"))

        # 检查 3：链接中包含敏感操作关键词
        if any(word in lowered for word in ["login", "password", "pay", "verify"]):
            hits.append(RuleHit("url", link, "medium", "链接中包含敏感操作关键词（登录/密码/支付）"))

    return hits


def _looks_like_ip_url(link: str) -> bool:
    """判断一个 URL 的主机名（域名部分）是不是 IP 地址。

    比如 http://192.168.1.1/admin 的主机名是 192.168.1.1，
    这就是一个 IP 地址。

    判断方法：把主机名按小数点分割，如果正好有 4 段，
    而且每段都是 0~255 之间的数字，就是 IP 地址。

    参数:
        link: 完整的 URL 字符串

    返回:
        True 如果主机名是 IP 地址
    """
    # 解析出主机名（域名/ IP 部分），过程如下：
    # "http://192.168.1.1:8080/path"
    #   1. split("://", 1) → ["http", "192.168.1.1:8080/path"]
    #   2. [-1] 取最后一部分 → "192.168.1.1:8080/path"
    #   3. split("/", 1)[0] → "192.168.1.1:8080"（去掉路径）
    #   4. split(":", 1)[0] → "192.168.1.1"（去掉端口号）
    host = link.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
    parts = host.split(".")

    # IP 地址必须由 4 段数字组成（如 192.168.1.1）
    if len(parts) != 4:
        return False

    # 检查每一段是否都是数字，且在 0~255 范围内
    for part in parts:
        if not part.isdigit():  # 不是纯数字
            return False
        val = int(part)
        if val < 0 or val > 255:  # IP 地址每段的范围是 0~255
            return False

    return True

#attachment是邮件的附件，后面的是这个参数的注解，代表要输入一个rulehit（字典类型）类型的列表
def _detect_attachment_risks(attachments: list[Any]) -> list[RuleHit]:
    """检测邮件附件是否存在安全风险。

    三种检测：
    1. 危险扩展名：附件是 .exe、.bat 等可执行文件
    2. 双扩展名伪装：文件名像 "invoice.doc.exe"，
       实际是 exe 文件，但伪装成 doc 文件
    3. 压缩包附件：.zip/.rar 等，里面可能藏着恶意文件

    Args:
        attachments: 附件列表，每个附件是一个字典，包含 filename 等字段

    Returns:
        风险指标列表
    """
    hits: list[RuleHit] = []
    for raw in attachments:
        # 检查格式：每个附件应该是一个字典（dict）
        # 如果不是字典就跳过（isinstance 是 Python 的类型检查函数）
        if not isinstance(raw, dict):
            continue
        filename = str(raw.get("filename") or "")
        if not filename:
            continue
        name_lower = filename.lower()

        # 提取文件扩展名（最后一个点后面的部分）
        # rfind(".") 从右往左找第一个点，找到最后一级扩展名
        ext = None
        dot = name_lower.rfind(".")
        if dot != -1:
            ext = name_lower[dot:]  # 例如 "document.pdf" → ".pdf"

        # 检查 1：危险扩展名（可执行文件）
        if ext and ext in _DANGEROUS_EXTENSIONS:
            hits.append(RuleHit(
                "attachment", filename, "high",
                f"发现危险可执行附件: {ext}",
            ))
            continue  # 已经判定为危险，跳过后续检查

        # 检查 2：双扩展名伪装
        # 比如 "resume.pdf.exe"——看起来像 PDF，实际上是 EXE
        if _DOUBLE_EXT_PATTERN.search(name_lower):
            hits.append(RuleHit(
                "attachment", filename, "high",
                "双扩展名文件，试图伪装成安全文件类型",
            ))
            continue

        # 检查 3：压缩包（里面可能藏病毒）
        if ext and ext in _ARCHIVE_EXTENSIONS:
            hits.append(RuleHit(
                "attachment", filename, "medium",
                "压缩包附件可能包含恶意脚本",
            ))
            continue

    return hits


def _detect_sender_spoofing(from_addr: str, from_name: str) -> list[RuleHit]:
    """检测发件人是否被伪造（钓鱼攻击的常见手段）。

    四种检测方法：
    1. 显示名称欺诈：发件人显示名称写了"PayPal"或"亚马逊"，
       但实际邮箱域名不是 paypal.com / amazon.com
    2. 域名抢注（typosquatting）：攻击者注册和知名域名很像的域名，
       比如 gmal.com 冒充 gmail.com，肉眼很难分辨
    3. 同形异码字符：用长得像的 Unicode 字符冒充，
       比如用西里尔字母的"а"（看起来是 a）代替英文字母 a
    4. IP 域名：发件人邮箱域名直接是 IP 地址（如 user@192.168.1.1）

    Args:
        from_addr: 发件人邮箱地址（如 "service@paypa1.com"）
        from_name: 发件人显示名称（如 "PayPal 客服中心"）

    Returns:
        风险指标列表
    """
    hits: list[RuleHit] = []
    if not from_addr:
        return hits

    from_name_stripped = from_name.strip()
    addr_lower = from_addr.strip().lower()

    # 从邮箱地址中提取 @ 后面的域名部分
    # "user@gmail.com" → "gmail.com"
    at_pos = addr_lower.rfind("@")
    if at_pos == -1:  # 没有 @ 符号，不是合法邮箱格式
        return hits
    domain = addr_lower[at_pos + 1:]

    # --- 检查 1：显示名称包含品牌名，但发件域名不属于该品牌 ---
    # 举例："亚马逊客服 <service@random123.com>"
    # 显示名称有"亚马逊"，但域名不是 amazon.com → 疑似钓鱼
    if from_name_stripped:
        name_lower = from_name_stripped.lower()
        # 找出显示名称中包含了哪些品牌名
        matched_brands = [b for b in _TRUSTED_BRANDS if b in name_lower]
        for brand in matched_brands:
            # 判断邮箱域名是否确实属于该品牌
            if not _domain_belongs_to_brand(domain, brand):
                hits.append(RuleHit(
                    "sender", f"{from_name_stripped} <{from_addr}>", "high",
                    f"显示名称包含'{brand}'，但发件域名'{domain}'与该品牌不匹配",
                ))

    # --- 检查 2：域名抢注（typosquatting）检测 ---
    # 遍历所有知名域名，看发件人域名是否和某个知名域名很像
    for known_domain in _KNOWN_DOMAINS:
        if _is_typosquatting(domain, known_domain):
            hits.append(RuleHit(
                "sender", from_addr, "high",
                f"域名'{domain}'与'{known_domain}'相似，疑似域名抢注",
            ))
            break  # 只要匹配一个就停止，避免重复报告
    else:
        # 这里的 else 属于 for 循环：只有当 for 循环"正常结束"
        # （没有 break）时才会执行。
        # 也就是说，只有没检测到 typosquatting 时，才继续检查同形字符。

        # --- 检查 3：域名中包含同形异码字符 ---
        if _has_homoglyph_chars(domain):
            hits.append(RuleHit(
                "sender", from_addr, "medium",
                f"域名'{domain}'包含同形异码字符（伪装字符）",
            ))

    # --- 检查 4：发件域名直接使用 IP 地址 ---
    # 正则表达式匹配像 192.168.1.1 这样的 IPv4 地址
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        hits.append(RuleHit(
            "sender", from_addr, "high",
            "发件邮箱使用裸 IP 地址作为域名",
        ))

    return hits


def _detect_phishing_text(text: str) -> list[RuleHit]:
    """检测邮件正文中是否包含钓鱼话术（phishing language）。

    钓鱼邮件通常会模仿官方通知的语气，使用"账户异常"、"请立即验证"、
    "您的账户将被停用"等话术来制造紧迫感和恐慌，诱导收件人点击链接。

    这个函数使用 _PHISHING_KEYWORDS 词库进行检测，和垃圾邮件检测的区别：
    - 垃圾邮件检测（_SPAM_KEYWORDS）影响 spam 标签
    - 钓鱼文本检测（_PHISHING_KEYWORDS）影响风险指标（risk indicators）

    Args:
        text: 邮件主题+正文（已转小写）

    Returns:
        检测到的风险指标列表
    """
    hits: list[RuleHit] = []
    if not text:
        return hits

    text_lower = text.lower()

    for weight, keywords in _PHISHING_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # 根据权重决定风险等级
                if weight >= 2.0:
                    level = "high"
                elif weight >= 1.0:
                    level = "medium"
                else:
                    level = "low"

                hits.append(RuleHit(
                    "phishing", keyword, level,
                    f"邮件文本包含钓鱼话术：'{keyword}'",
                ))

    return hits


def _detect_html_risks(html_content: str) -> list[RuleHit]:
    """检测 HTML 邮件内容中的安全风险。

    接口文档要求分析 HTML 正文，因此这个函数专门处理 HTML 相关的检测：
    1. 隐藏内容：使用 display:none 等 CSS 隐藏的文字（常用于垃圾邮件）
    2. 跟踪像素：1x1 像素的透明图片（用于追踪用户是否打开邮件）
    3. 外部图片：加载外部图片可能泄露用户 IP 和阅读行为

    Args:
        html_content: 邮件的 HTML 正文

    Returns:
        风险指标列表
    """
    hits: list[RuleHit] = []
    if not html_content:
        return hits

    html_lower = html_content.lower()

    # 检查 1：隐藏内容（display:none 或 visibility:hidden）
    # 垃圾邮件经常把一段文字隐藏起来，只让关键词被检测到
    if "display:none" in html_lower or "visibility:hidden" in html_lower:
        hits.append(RuleHit(
            "html", "hidden_content", "medium",
            "HTML 中包含 CSS 隐藏的文本内容",
        ))

    # 检查 2：检测跟踪像素（1x1 像素的图片）
    # 正则匹配 <img ... width="1" height="1" ...>
    if re.search(r'width\s*=\s*["\']?\s*1\s*["\']?\s+height\s*=\s*["\']?\s*1\s*["\']?', html_lower):
        hits.append(RuleHit(
            "html", "tracking_pixel", "low",
            "邮件包含跟踪像素（1×1 透明图片），可能用于追踪阅读行为",
        ))

    # 检查 3：统计外部图片数量，超过一定数量视为可疑
    img_count = len(re.findall(r'<img[^>]+src\s*=\s*["\']https?://', html_lower))
    if img_count > 3:
        hits.append(RuleHit(
            "html", "external_images", "low",
            f"邮件包含 {img_count} 个外部图片链接，可能泄露阅读行为",
        ))

    return hits


def _domain_belongs_to_brand(domain: str, brand: str) -> bool:
    """判断某个域名是否属于某个品牌的合法域名。

    这里维护了一个品牌名 → 合法域名列表的映射表。
    比如品牌 "google" 的合法域名包括 google.com 和 gmail.com。

    如果发件人自称是"Google"但邮箱是 user@random.com，这个函数会返回 False。

    Args:
        domain: 要检查的域名（如 "gmail.com"）
        brand:  品牌名（如 "google"）

    Returns:
        True 表示该域名确实是该品牌的合法域名
    """
    brand_to_domains = {
        "amazon": {"amazon.com", "amazon.co.uk", "amazon.de", "amazon.cn", "aws.amazon.com"},
        "apple": {"apple.com", "icloud.com"},
        "google": {"google.com", "gmail.com"},
        "microsoft": {"microsoft.com", "outlook.com", "hotmail.com"},
        "paypal": {"paypal.com"},
        "支付宝": {"alipay.com"},
        "微信": {"wechat.com", "qq.com"},
        "腾讯": {"qq.com", "tencent.com", "weixin.com"},
        "linkedin": {"linkedin.com"},
        "github": {"github.com"},
        "slack": {"slack.com"},
        "zoom": {"zoom.us"},
        "adobe": {"adobe.com"},
        "netflix": {"netflix.com"},
        "华为": {"huawei.com"},
        "小米": {"xiaomi.com"},
    }
    allowed = brand_to_domains.get(brand, set())
    return domain in allowed


def _is_typosquatting(domain: str, known: str) -> bool:
    """检测一个域名是否在"抢注"（typosquatting）知名域名。

    什么是 typosquatting？
    攻击者注册一个和知名域名很像的域名，比如：
    - gmal.com（gmail.com 少了 i）
    - gggmail.com（多了一个字母）
    - gma1l.com（用数字 1 代替字母 l）
    - gmail.com.evil.com（把知名域名放在子域名位置迷惑人）

    当用户手滑输错或者没仔细看，就可能进入攻击者的网站。

    检测方法：
    1. 如果 domain 以 "known." 开头（如 gmail.com.evil.com），判定为抢注
    2. 如果编辑距离 ≤ 2（增/删/改不超过 2 个字符），判定为抢注
    3. 如果去掉点号后完全相同（gmailcom 冒充 gmail.com），判定为抢注

    Args:
        domain: 要检查的域名
        known:  对照的知名域名

    Returns:
        True 表示疑似域名抢注
    """

    # 完全相同的域名不是抢注（就是它本身）
    if domain == known:
        return False

    # 检查手法 1：知名域名作为子域名前缀
    # 比如 domain = "gmail.com.evil.com"，它以 "gmail.com." 开头
    # 攻击者注册了 evil.com，然后在前面加了个 gmail.com 子域名来迷惑人
    if domain.startswith(known + ".") and len(domain) > len(known) + 1:
        return True

    # 检查手法 2：编辑距离 ≤ 2
    # 编辑距离是指把一个字符串变成另一个字符串需要的最少操作次数。
    # 操作包括：插入一个字符、删除一个字符、替换一个字符。
    # 比如 "gmail" → "gmal" 需要 1 次删除，编辑距离 = 1
    dist = _edit_distance(domain, known)
    if dist <= 2:
        return True

    # 检查手法 3：去掉点号后相同
    # 比如 "gmailcom" 去掉点号还是 "gmailcom"
    # 而 "gmail.com" 去掉点号也是 "gmailcom"
    # 所以认为 "gmailcom" 在冒充 "gmail.com"
    known_without_dot = known.replace(".", "")
    domain_without_dot = domain.replace(".", "")
    if known_without_dot == domain_without_dot:
        return True

    return False


def _edit_distance(a: str, b: str) -> int:
    """计算两个字符串之间的"编辑距离"（Levenshtein distance）。

    编辑距离是一个经典算法问题，在很多教科书中都有讲解。

    定义：把字符串 A 变成字符串 B，最少需要多少次"编辑操作"。
    编辑操作有三种：
    1. 插入一个字符（比如 "googl" → "google" 插入 e）
    2. 删除一个字符（比如 "gmail" → "gmal" 删除 i）
    3. 替换一个字符（比如 "gmail" → "gmaxl" 把 i 换成 x）

    算法原理（动态规划）：
    用一个二维表格 dp[i][j] 表示"把 a[:i] 变成 b[:j] 需要的最少步数"。
    表格的每个格子由它左边、上边、左上角的三个格子的值计算得出。

    例如计算 "abc" → "ab" 的编辑距离：

             ""   a   b
        ""   0   1   2
        a    1   0   1
        b    2   1   0
        c    3   2   1  ← 答案是 1（删除 c）

    为了节省内存，这里没有用完整的二维表格，而是只用了两行（prev 和 curr），
    这是动态规划中常见的"滚动数组"优化技巧。

    Args:
        a: 第一个字符串
        b: 第二个字符串

    Returns:
        编辑距离（整数），值越大表示两个字符串差异越大
    """
    m, n = len(a), len(b)

    # 这里做了一个优化：让 m 始终是较短的那个字符串的长度
    # 这样可以减少内存占用（只需要 m+1 长度的数组）
    if m > n:
        a, b = b, a
        m, n = n, m

    # prev[j] 代表表格的"上一行"的第 j 列
    # 初始化：把空字符串变成 a[:j] 需要 j 次插入操作
    prev = list(range(m + 1))

    # 一行一行地计算（j 从 1 到 n）
    for j in range(1, n + 1):
        # curr[0] = j，因为把 a[:0]（空串）变成 b[:j] 需要 j 次插入
        curr = [j] + [0] * m
        for i in range(1, m + 1):
            # 如果 a[i-1] == b[j-1]，当前字符相同，不需要替换操作
            # 否则需要 1 次替换操作
            cost = 0 if a[i - 1] == b[j - 1] else 1
            # dp 状态转移方程：
            # curr[i-1] + 1:   删除 a[i-1]（从左边的格子来）
            # prev[i] + 1:     插入 b[j-1]（从上边的格子来）
            # prev[i-1] + cost: 替换或不操作（从左上角的格子来）
            # 取三种操作中最小的那个
            curr[i] = min(curr[i - 1] + 1, prev[i] + 1, prev[i - 1] + cost)
        # 当前行变成上一行，继续计算下一行
        prev = curr

    # 最终答案在 prev[m]：把整个 a 变成整个 b 需要的最少步数
    return prev[m]


def _has_homoglyph_chars(text: str) -> bool:
    """检测字符串中是否包含"同形异码"（homoglyph）Unicode 字符。

    什么是同形异码？
    在 Unicode 编码中，不同的字符可能看起来长得一模一样。
    比如英文字母 'a'（U+0061）和西里尔字母 'а'（U+0430）看起来几乎一样，
    但在计算机内部是完全不同的编码。

    攻击者利用这一点：用看起来和英文字母一样但编码不同的字符注册域名，
    比如用西里尔字母注册 "gmаil.com"（第二个 а 是西里尔字母），
    用户看起来是 gmail.com，实际去了攻击者的网站。

    检测方法：
    检查字符串中每个字符的 Unicode 编码是否在"可疑范围"内。
    这些范围包括西里尔字母、希腊字母、全角字符等，
    它们里面有些字符和英文字母长得几乎一样。

    Args:
        text: 要检查的字符串

    Returns:
        True 表示包含可疑的同形异码字符
    """
    # 可疑的 Unicode 字符范围列表，每个元素是（起始码点，结束码点）
    suspicious_ranges = [
        (0x00A0, 0x00BF),  # Latin-1 补充：不换行空格等特殊符号
        (0x0130, 0x024F),  # 拉丁文扩展：İ, Ŋ 等扩展拉丁字母
        (0x1D00, 0x1D7F),  # 音标扩展：看起来像字母的音标符号
        (0x1E00, 0x1EFF),  # 拉丁文扩展附加：更多拉丁字母变体
        (0x2C60, 0x2C7F),  # 拉丁文扩展-C
        (0xFF00, 0xFFEF),  # 全角字符：在中文输入法下打出的英文字母属于这个范围
                           # 比如全角 Ａ（FF21）和半角 A（0041）看起来一样
        (0x0400, 0x04FF),  # 西里尔字母（俄语字母）：很多和英文字母形状相同
                           # 比如西里尔字母 а（0430）和英文字母 a（0061）
        (0x0370, 0x03FF),  # 希腊字母：部分和英文字母长得一样
                           # 比如希腊字母 ο（Ώ）和英文字母 o（006F）
    ]

    for ch in text:
        cp = ord(ch)  # ord() 获取字符的 Unicode 码点（整数）
        for lo, hi in suspicious_ranges:
            # 如果这个字符的码点在某个可疑范围内
            if lo <= cp <= hi:
                return True

    # 所有字符都不在可疑范围内
    return False
