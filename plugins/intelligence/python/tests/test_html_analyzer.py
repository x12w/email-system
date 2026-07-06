from __future__ import annotations

from src.html_analyzer import (
    analyze_html_content,
    count_external_images,
    detect_hidden_content,
    detect_tracking_pixels,
    extract_links_from_html,
    extract_text_from_html,
)


class TestExtractTextFromHtml:
    """测试从 HTML 提取纯文本。"""

    def test_empty_html(self):
        assert extract_text_from_html("") == ""

    def test_none_html(self):
        assert extract_text_from_html(None) == ""

    def test_plain_text_passthrough(self):
        """无标签的纯文本应原样返回"""
        assert extract_text_from_html("Hello World") == "Hello World"

    def test_strip_simple_tags(self):
        """简单标签应被移除"""
        assert extract_text_from_html("<p>Hello</p>") == "Hello"

    def test_script_content_removed(self):
        """script 标签内的内容不应出现在结果中"""
        result = extract_text_from_html("<script>alert('xss')</script><p>Hello</p>")
        assert "alert" not in result
        assert result == "Hello"

    def test_style_content_removed(self):
        """style 标签内的内容不应出现在结果中"""
        result = extract_text_from_html("<style>.hidden{display:none}</style><p>Visible</p>")
        assert "display" not in result
        assert result == "Visible"

    def test_comments_removed(self):
        """HTML 注释应被移除"""
        result = extract_text_from_html("<!-- comment --><p>Text</p>")
        assert "comment" not in result
        assert result == "Text"

    def test_block_tags_to_newlines(self):
        """块级标签应被替换为换行符"""
        result = extract_text_from_html("<p>Line1</p><p>Line2</p>")
        assert "Line1" in result
        assert "Line2" in result

    def test_multiple_whitespace_collapsed(self):
        """连续空白应被合并"""
        result = extract_text_from_html("<p>Hello    World</p>")
        assert result == "Hello World"

    def test_nested_tags(self):
        """嵌套标签应正确展平"""
        result = extract_text_from_html("<div><p>Hello <b>World</b></p></div>")
        assert result == "Hello World"

    def test_br_tag_newline(self):
        """<br> 标签应产生换行"""
        result = extract_text_from_html("Line1<br>Line2")
        # 结果中两个单词应同时存在
        assert "Line1" in result
        assert "Line2" in result

    def test_self_closing_tags(self):
        """自闭合标签应正确处理"""
        result = extract_text_from_html("<img src='img.png'><p>Text</p>")
        assert result == "Text"


class TestDetectHiddenContent:
    """测试 HTML 隐藏内容检测。"""

    def test_empty_html(self):
        assert detect_hidden_content("") == []

    def test_no_hidden(self):
        """无隐藏样式的 HTML 应返回空列表"""
        result = detect_hidden_content("<p>Visible text</p>")
        assert result == []

    def test_display_none(self):
        """display:none 应被检测"""
        result = detect_hidden_content('<div style="display:none">Hidden</div>')
        assert len(result) >= 1
        assert result[0]["type"] == "hidden_element"

    def test_visibility_hidden(self):
        """visibility:hidden 应被检测"""
        result = detect_hidden_content('<span style="visibility:hidden">Invisible</span>')
        assert len(result) >= 1

    def test_opacity_0(self):
        """opacity:0 应被检测"""
        result = detect_hidden_content('<span style="opacity:0">Transparent</span>')
        assert len(result) >= 1

    def test_multiple_hidden(self):
        """多个隐藏元素都应被检测"""
        html = '<div style="display:none">A</div><span style="visibility:hidden">B</span>'
        result = detect_hidden_content(html)
        assert len(result) == 2

    def test_tag_name_in_result(self):
        """结果应包含标签名"""
        result = detect_hidden_content('<div style="display:none">X</div>')
        assert result[0]["tag"] == "div"


class TestCountExternalImages:
    """测试统计外部图片数量。"""

    def test_empty_html(self):
        assert count_external_images("") == 0

    def test_no_images(self):
        assert count_external_images("<p>Text</p>") == 0

    def test_single_image(self):
        assert count_external_images('<img src="https://example.com/img.png">') == 1

    def test_multiple_images(self):
        html = '<img src="a.png"><img src="b.png"><img src="c.png">'
        assert count_external_images(html) == 3

    def test_images_in_tags(self):
        """非 img 标签中的 src 不应计数"""
        html = '<a src="link.png">test</a>'
        assert count_external_images(html) == 0


class TestDetectTrackingPixels:
    """测试跟踪像素检测。"""

    def test_empty_html(self):
        assert detect_tracking_pixels("") == []

    def test_no_tracking_pixel(self):
        """正常图片不应被误判为跟踪像素"""
        result = detect_tracking_pixels('<img src="photo.jpg" width="800" height="600">')
        assert result == []

    def test_width_1_tracking(self):
        """宽为 1 的图片应被检测为跟踪像素"""
        result = detect_tracking_pixels('<img src="track.png" width="1" height="1">')
        assert len(result) >= 1
        assert result[0]["type"] == "tracking_pixel"

    def test_tracking_pixel_fields(self):
        """跟踪像素结果应包含 src、width、height"""
        result = detect_tracking_pixels('<img src="pixel.gif" width="1" height="1">')
        assert result[0]["src"] == "pixel.gif"
        assert result[0]["width"] == 1
        assert result[0]["height"] == 1


class TestExtractLinksFromHtml:
    """测试从 HTML 提取链接。"""

    def test_empty_html(self):
        assert extract_links_from_html("") == []

    def test_no_links(self):
        assert extract_links_from_html("<p>No links here</p>") == []

    def test_single_link(self):
        html = '<a href="https://example.com">Click</a>'
        assert extract_links_from_html(html) == ["https://example.com"]

    def test_multiple_links(self):
        html = '<a href="https://a.com">A</a><a href="https://b.com">B</a>'
        assert extract_links_from_html(html) == ["https://a.com", "https://b.com"]

    def test_relative_and_absolute(self):
        html = '<a href="/relative">Rel</a><a href="https://abs.com">Abs</a>'
        assert extract_links_from_html(html) == ["/relative", "https://abs.com"]


class TestAnalyzeHtmlContent:
    """测试 HTML 综合分析。"""

    def test_empty_html(self):
        """空 HTML 应返回各字段均为空的字典"""
        result = analyze_html_content("")
        assert result["plain_text"] == ""
        assert result["hidden_elements"] == []
        assert result["external_images"] == 0
        assert result["tracking_pixels"] == []
        assert result["extracted_links"] == []
        assert result["has_hidden_content"] is False
        assert result["has_tracking_pixel"] is False

    def test_plain_text_extracted(self):
        """纯文本应被正确提取"""
        result = analyze_html_content("<p>Hello World</p>")
        assert result["plain_text"] == "Hello World"

    def test_hidden_content_detected(self):
        """隐藏内容应被检测"""
        result = analyze_html_content('<div style="display:none">Hidden</div>')
        assert result["has_hidden_content"] is True
        assert len(result["hidden_elements"]) >= 1

    def test_external_images_counted(self):
        """外部图片应被计数"""
        result = analyze_html_content('<img src="a.png"><img src="b.png">')
        assert result["external_images"] == 2

    def test_links_extracted(self):
        """链接应被提取"""
        result = analyze_html_content('<a href="https://example.com">Link</a>')
        assert "https://example.com" in result["extracted_links"]

    def test_tracking_pixels_detected(self):
        """跟踪像素应被检测"""
        result = analyze_html_content('<img src="pixel.gif" width="1" height="1">')
        assert result["has_tracking_pixel"] is True
