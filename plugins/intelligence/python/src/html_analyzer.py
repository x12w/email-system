from __future__ import annotations

import re
from typing import Any


# ============================================================
# HTML 邮件内容分析模块
# ============================================================
#
# 很多邮件使用 HTML 格式，而不是纯文本。
# HTML 邮件可能包含：
#   - 隐藏文字（display:none 或 visibility:hidden 的文字，对用户不可见
#     但搜索引擎和过滤器能看到，攻击者常用来"塞"关键词）
#   - 跟踪像素（1x1 的透明图片，用于追踪用户是否打开了邮件）
#   - 混淆链接（显示的文字是一个地址，实际链接指向另一个地址）
#   - 外部资源（加载远程图片、字体等，可能泄露用户隐私）
#
# 这个模块提供对 HTML 邮件的分析功能。


# 匹配 HTML 标签的正则表达式
# 例如 <div class="content"> 会被匹配
_RE_HTML_TAG = re.compile(r"<[^>]+>")

# 匹配 HTML 注释 <!-- ... -->
_RE_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")

# 匹配 style 标签及其内容
_RE_STYLE_BLOCK = re.compile(r"<style[^>]*>[\s\S]*?</style>", re.IGNORECASE)

# 匹配 script 标签及其内容
_RE_SCRIPT_BLOCK = re.compile(r"<script[^>]*>[\s\S]*?</script>", re.IGNORECASE)

# 匹配隐藏样式：display:none、visibility:hidden、opacity:0 等
_RE_HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none"
    r"|visibility\s*:\s*hidden"
    r"|opacity\s*:\s*0"
    r"|width\s*:\s*0\s*px"
    r"|height\s*:\s*0\s*px",
    re.IGNORECASE,
)

# 匹配 1x1 像素的图片（跟踪像素的特征）
_RE_TRACKING_PIXEL = re.compile(
    r'<img[^>]*(?:width\s*=\s*["\']?\s*1\s*["\']?)?[^>]*(?:height\s*=\s*["\']?\s*1\s*["\']?)?[^>]*/?>',
    re.IGNORECASE,
)

# 匹配 HTML 中的链接 <a href="...">
_RE_HTML_LINK = re.compile(r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)

# 匹配图片标签 <img src="...">
_RE_IMG_SRC = re.compile(r'<img\s+[^>]*src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)


def extract_text_from_html(html_content: str) -> str:
    """从 HTML 内容中提取纯文本。

    工作流程：
    1. 先移除 script 和 style 标签里面的内容（里面通常没有可见文字）
    2. 再移除 HTML 注释
    3. 把 <br>、</p>、</div> 等块级标签替换成换行符
    4. 去掉所有剩余的 HTML 标签
    5. 把多个空白字符合并成一个空格
    6. 去掉首尾的空白

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        提取出的纯文本字符串
    """
    if not html_content:
        return ""

    text = html_content

    # 第一步：移除 script 和 style 块（它们的内容不是用户看到的文字）
    text = _RE_SCRIPT_BLOCK.sub("", text)
    text = _RE_STYLE_BLOCK.sub("", text)

    # 第二步：移除 HTML 注释
    text = _RE_HTML_COMMENT.sub("", text)

    # 第三步：把块级标签替换成换行符，保证提取的文字换行正确
    # 比如 <p>第一行</p><p>第二行</p> → "第一行\n第二行"
    for block_tag in ["</p>", "</div>", "</li>", "</tr>", "</h\\d>", "<br", "</blockquote>"]:
        text = re.sub(block_tag, "\n", text, flags=re.IGNORECASE)

    # 第四步：去掉所有剩余的 HTML 标签
    text = _RE_HTML_TAG.sub("", text)

    # 第五步：把连续空白（空格、换行、制表符等）合并成一个空格
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detect_hidden_content(html_content: str) -> list[dict[str, Any]]:
    """检测 HTML 中的隐藏内容。

    常见手法：
    - display: none（元素完全隐藏）
    - visibility: hidden（元素不可见但占位）
    - opacity: 0（完全透明）
    - font-size: 0 或 1px（文字极小，肉眼看不见）
    - 把文字颜色设成和背景色一样

    攻击者使用这些手法把大量关键词"藏"在页面里，
    试图欺骗垃圾邮件过滤器但又不想让用户看到。

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        检测到的隐藏内容列表，每项包含类型、位置、内容摘要
    """
    results: list[dict[str, Any]] = []
    if not html_content:
        return results

    # 查找所有元素标签（包含 style 属性的）
    # 这里用简单的正则匹配，不解析完整的 HTML DOM
    hidden_pattern = re.compile(
        r"<(\w+)[^>]*style\s*=\s*[\"\'][^\"\']*?(display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0)[^\"\']*[\"\'][^>]*>",
        re.IGNORECASE,
    )
    for match in hidden_pattern.finditer(html_content):
        tag_name = match.group(1)
        style_content = match.group(2)
        results.append({
            "type": "hidden_element",
            "tag": tag_name,
            "style": style_content,
            "html_snippet": match.group()[:100],  # 截取前 100 个字符
        })

    return results


def count_external_images(html_content: str) -> int:
    """统计 HTML 中外部图片的数量。

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        外部图片总数
    """
    if not html_content:
        return 0
    return len(_RE_IMG_SRC.findall(html_content))


def detect_tracking_pixels(html_content: str) -> list[dict[str, Any]]:
    """检测 HTML 中是否有跟踪像素（tracking pixels）。

    跟踪像素通常是一张 1x1 像素的透明图片，用于追踪：
    - 用户是否打开了邮件
    - 打开邮件的 IP 地址
    - 打开邮件的时间
    - 使用的设备类型

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        检测到的跟踪像素列表
    """
    results: list[dict[str, Any]] = []
    if not html_content:
        return results

    # 匹配可能的跟踪像素：宽或高为 1 的图片，或者没有 width/height 属性
    # 但带有 src 属性的小图片
    pixel_pattern = re.compile(
        r'<img\s+[^>]*?src\s*=\s*["\']([^"\']+)["\'][^>]*?>',
        re.IGNORECASE,
    )

    for match in pixel_pattern.finditer(html_content):
        img_tag = match.group(0)
        src = match.group(1)

        # 检查是否是明显的跟踪像素
        # 有 width=1 / height=1 的特征
        is_pixel = bool(re.search(r'width\s*=\s*["\']?\s*["\']?["\']?', img_tag))

        width_match = re.search(r'width\s*=\s*["\']?(\d+)["\']?', img_tag, re.IGNORECASE)
        height_match = re.search(r'height\s*=\s*["\']?(\d+)["\']?', img_tag, re.IGNORECASE)

        w = int(width_match.group(1)) if width_match else 0
        h = int(height_match.group(1)) if height_match else 0

        # 宽或高 ≤ 1 像素 → 极可能是跟踪像素
        if (w <= 1 and h <= 1) or (w == 0 and h == 0 and "pixel" in src.lower()):
            results.append({
                "src": src,
                "width": w,
                "height": h,
                "type": "tracking_pixel",
            })

    return results


def extract_links_from_html(html_content: str) -> list[str]:
    """从 HTML 邮件中提取所有链接（<a href="...">）。

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        链接地址列表
    """
    if not html_content:
        return []
    return _RE_HTML_LINK.findall(html_content)


def analyze_html_content(html_content: str) -> dict[str, Any]:
    """综合分析 HTML 内容，返回分析结果。

    一次性完成多项检测，避免重复解析 HTML。

    Args:
        html_content: 原始的 HTML 字符串

    Returns:
        包含各项分析结果的字典：
        - plain_text: 提取的纯文本
        - hidden_elements: 检测到的隐藏元素
        - external_images: 外部图片数量
        - tracking_pixels: 跟踪像素列表
        - extracted_links: HTML 中的链接
        - has_hidden_content: 是否存在隐藏内容（布尔值）
        - has_tracking_pixel: 是否存在跟踪像素（布尔值）
    """
    result: dict[str, Any] = {
        "plain_text": "",
        "hidden_elements": [],
        "external_images": 0,
        "tracking_pixels": [],
        "extracted_links": [],
        "has_hidden_content": False,
        "has_tracking_pixel": False,
    }

    if not html_content:
        return result

    result["plain_text"] = extract_text_from_html(html_content)
    result["hidden_elements"] = detect_hidden_content(html_content)
    result["external_images"] = count_external_images(html_content)
    result["tracking_pixels"] = detect_tracking_pixels(html_content)
    result["extracted_links"] = extract_links_from_html(html_content)
    result["has_hidden_content"] = len(result["hidden_elements"]) > 0
    result["has_tracking_pixel"] = len(result["tracking_pixels"]) > 0

    return result
