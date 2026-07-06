#!/usr/bin/env python3
"""Generate project presentation PPT for Email System."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# Color scheme
PRIMARY = RGBColor(0x1A, 0x56, 0xDB)     # Blue
SECONDARY = RGBColor(0x10, 0x98, 0xAD)    # Teal
ACCENT = RGBColor(0xF5, 0xA6, 0x23)       # Orange
DARK = RGBColor(0x1E, 0x29, 0x3B)         # Dark navy
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG = RGBColor(0xF3, 0xF4, 0xF6)
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)
TEXT_GRAY = RGBColor(0x66, 0x66, 0x66)
GREEN = RGBColor(0x10, 0xB9, 0x81)
RED = RGBColor(0xEF, 0x44, 0x44)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_bg(slide, color):
    """Set slide background color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, left, top, width, height, color, opacity=None):
    """Add a colored rectangle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_textbox(slide, left, top, width, height, text, font_size=18,
                color=TEXT_DARK, bold=False, alignment=PP_ALIGN.LEFT,
                font_name='Microsoft YaHei'):
    """Add a text box with single style."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_multiline_box(slide, left, top, width, height, lines, font_name='Microsoft YaHei'):
    """Add a text box with multiple styled lines.
    lines: list of (text, font_size, color, bold, alignment)
    """
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line_data in enumerate(lines):
        text, font_size, color, bold = line_data[:4]
        alignment = line_data[4] if len(line_data) > 4 else PP_ALIGN.LEFT
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = text
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.font.name = font_name
        p.alignment = alignment
        p.space_after = Pt(4)
    return txBox


def add_section_header(slide, title, subtitle=""):
    """Add consistent section header."""
    # Top accent bar
    add_rect(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.08), PRIMARY)
    # Title
    add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11), Inches(0.8),
                title, font_size=36, color=DARK, bold=True)
    if subtitle:
        add_textbox(slide, Inches(0.8), Inches(1.1), Inches(11), Inches(0.5),
                    subtitle, font_size=16, color=TEXT_GRAY)
    # Separator line
    add_rect(slide, Inches(0.8), Inches(1.5), Inches(11.5), Inches(0.03), PRIMARY)


def add_footer(slide, page_num):
    """Add page number footer."""
    add_textbox(slide, Inches(12), Inches(7.0), Inches(1), Inches(0.4),
                str(page_num), font_size=10, color=TEXT_GRAY, alignment=PP_ALIGN.RIGHT)


def add_card(slide, left, top, width, height, title, items, icon_color=PRIMARY):
    """Add a card with title and bullet items."""
    # Card background
    card = add_rect(slide, left, top, width, height, WHITE)
    card.shadow.inherit = False
    # Card left accent
    add_rect(slide, left, top, Inches(0.06), height, icon_color)
    # Title
    add_textbox(slide, left + Inches(0.25), top + Inches(0.15), width - Inches(0.5), Inches(0.4),
                title, font_size=18, color=DARK, bold=True)
    # Items
    y = top + Inches(0.6)
    for item in items:
        add_textbox(slide, left + Inches(0.4), y, width - Inches(0.7), Inches(0.3),
                    f"• {item}", font_size=13, color=TEXT_DARK)
        y += Inches(0.28)


# ============================================================
# SLIDE 1: Title Slide
# ============================================================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
add_bg(slide1, DARK)

# Decorative shapes
add_rect(slide1, Inches(0), Inches(0), prs.slide_width, Inches(0.12), PRIMARY)
add_rect(slide1, Inches(0), Inches(7.38), prs.slide_width, Inches(0.12), PRIMARY)
add_rect(slide1, Inches(0), Inches(3.2), Inches(0.12), Inches(1.1), ACCENT)

# Title
add_textbox(slide1, Inches(1.5), Inches(1.8), Inches(10), Inches(1.2),
            "电子邮件系统", font_size=56, color=WHITE, bold=True)

# Subtitle
add_textbox(slide1, Inches(1.5), Inches(3.0), Inches(10), Inches(0.6),
            "Email System — 智能邮件管理平台", font_size=24, color=SECONDARY)

# Description
add_multiline_box(slide1, Inches(1.5), Inches(3.8), Inches(10), Inches(1.5), [
    ("基于 Spring Boot + Vue 3 的全栈邮件系统", 18, RGBColor(0xBB, 0xBB, 0xBB), False),
    ("支持 SMTP/IMAP 收发信、智能垃圾检测、风险识别、多租户隔离", 18, RGBColor(0xBB, 0xBB, 0xBB), False),
    ("", 10, WHITE, False),
    ("项目汇报", 20, ACCENT, True),
    ("2026 年 7 月", 14, TEXT_GRAY, False),
])

# Tech stack pills
pill_data = [
    ("Vue 3", Inches(1.5)), ("Spring Boot", Inches(3.3)), ("MySQL", Inches(5.9)),
    ("Redis", Inches(7.5)), ("Docker", Inches(9.0)), ("Python AI", Inches(10.8)),
]
for text, left in pill_data:
    pill = add_rect(slide1, left, Inches(5.8), Inches(1.5), Inches(0.5), PRIMARY)
    pill.text = text
    pill.text_frame.paragraphs[0].font.size = Pt(12)
    pill.text_frame.paragraphs[0].font.color.rgb = WHITE
    pill.text_frame.paragraphs[0].font.bold = True
    pill.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    pill.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

add_footer(slide1, 1)

# ============================================================
# SLIDE 2: 项目概述
# ============================================================
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide2, LIGHT_BG)
add_section_header(slide2, "项目概述", "Project Overview")

# Overview cards
add_card(slide2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.3),
         "项目定位", [
             "全栈电子邮件管理系统",
             "支持多邮箱账号绑定与统一管理",
             "集成 AI 智能邮件分析与风险检测",
             "面向个人及小团队的生产力工具",
         ], PRIMARY)

add_card(slide2, Inches(6.9), Inches(1.8), Inches(5.6), Inches(2.3),
         "核心能力", [
             "SMTP/IMAP 邮件收发（支持 Gmail/QQ/Outlook/163）",
             "智能垃圾邮件过滤 + 优先级识别 + 风险检测",
             "Python 插件化 AI 引擎，可热替换模型",
             "多租户用户隔离，独立邮箱账号管理",
         ], SECONDARY)

add_card(slide2, Inches(0.8), Inches(4.4), Inches(5.6), Inches(2.3),
         "技术选型", [
             "前端：Vue 3 + TypeScript + Element Plus + Pinia",
             "后端：Spring Boot 3 + Spring Security + JWT",
             "持久层：MySQL 8.0 + MyBatis-Plus + Redis",
             "存储：MinIO 对象存储 / 本地文件系统可选",
         ], GREEN)

add_card(slide2, Inches(6.9), Inches(4.4), Inches(5.6), Inches(2.3),
         "部署与运维", [
             "Docker Compose 一键启动全部服务",
             "Nginx 反向代理 + 前端静态资源",
             "Mailpit 本地邮件测试",
             "健康检查、登录审计、限流保护",
         ], ACCENT)

add_footer(slide2, 2)

# ============================================================
# SLIDE 3: 系统架构
# ============================================================
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide3, LIGHT_BG)
add_section_header(slide3, "系统架构", "System Architecture")

# Architecture layers as visual blocks
layers = [
    ("展示层", "Vue 3 + TypeScript + Vite\nElement Plus + Pinia\nAxios HTTP Client", PRIMARY),
    ("网关层", "Nginx 反向代理\n静态资源服务\nAPI /api/ 转发", RGBColor(0x6C, 0x75, 0x7D)),
    ("应用层", "Spring Boot REST API\nSpring Security + JWT\n统一响应 / 异常处理", SECONDARY),
    ("业务层", "邮件收发 · 文件夹同步\n智能分析编排 · 联系人管理\n推送事件 · 附件管理", GREEN),
    ("数据层", "MySQL 8.0 · Redis 7\nMinIO 对象存储\nFlyway 数据库迁移", ACCENT),
    ("AI 引擎", "Python Native 插件 (.so/.dll)\n垃圾检测 · 优先级 · 风险识别\n超时熔断 · 版本管理", RGBColor(0x8E, 0x44, 0xAD)),
]

y_pos = Inches(1.8)
for name, desc, color in layers:
    # Layer name block
    block = add_rect(slide3, Inches(0.8), y_pos, Inches(2.5), Inches(0.75), color)
    block.text = name
    block.text_frame.paragraphs[0].font.size = Pt(16)
    block.text_frame.paragraphs[0].font.color.rgb = WHITE
    block.text_frame.paragraphs[0].font.bold = True
    block.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    block.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Description
    add_multiline_box(slide3, Inches(3.6), y_pos + Inches(0.05), Inches(8.5), Inches(0.7), [
        (line, 13, TEXT_DARK, False) for line in desc.split('\n')
    ])

    # Arrow (except last)
    if y_pos < Inches(5.5):
        arrow = add_rect(slide3, Inches(0.8), y_pos + Inches(0.82), Inches(2.5), Inches(0.06), color)

    y_pos += Inches(0.9)

add_footer(slide3, 3)

# ============================================================
# SLIDE 4: 核心功能模块
# ============================================================
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide4, LIGHT_BG)
add_section_header(slide4, "核心功能模块", "Core Features")

modules = [
    ("用户认证与安全", PRIMARY, [
        "JWT 双 Token 机制 (access + refresh)",
        "登录限流 (5次/分钟)",
        "登录审计日志",
        "显式 CORS 配置",
        "密码 BCrypt 加密存储",
    ]),
    ("邮件收发管理", SECONDARY, [
        "多邮箱账号绑定 (SMTP + IMAP)",
        "SSL/TLS 加密传输",
        "邮件文件夹同步与未读数",
        "邮件搜索、筛选、分页",
        "草稿保存、已读/未读标记",
    ]),
    ("智能邮件分析", GREEN, [
        "垃圾邮件自动识别 (spam/normal)",
        "优先级智能分级 (high/normal/low)",
        "风险检测 (恶意链接/钓鱼/高危附件)",
        "Python 插件 ABI，2s 超时熔断",
        "分析结果可视化 + 推送通知",
    ]),
    ("联系人与附件", ACCENT, [
        "联系人 CRUD + 自动补全",
        "附件上传/下载/预览",
        "MinIO 对象存储 + 本地存储",
        "附件校验和完整性检查",
    ]),
]

x_start = Inches(0.6)
for i, (title, color, items) in enumerate(modules):
    left = x_start + Inches(i * 3.1)
    # Module card
    add_rect(slide4, left, Inches(1.8), Inches(2.9), Inches(5.0), WHITE)
    # Header
    header = add_rect(slide4, left, Inches(1.8), Inches(2.9), Inches(0.7), color)
    header.text = title
    header.text_frame.paragraphs[0].font.size = Pt(16)
    header.text_frame.paragraphs[0].font.color.rgb = WHITE
    header.text_frame.paragraphs[0].font.bold = True
    header.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    header.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    y_item = Inches(2.7)
    for item in items:
        add_textbox(slide4, left + Inches(0.2), y_item, Inches(2.5), Inches(0.35),
                    f"▸ {item}", font_size=12, color=TEXT_DARK)
        y_item += Inches(0.4)

add_footer(slide4, 4)

# ============================================================
# SLIDE 5: 智能邮件管理详解
# ============================================================
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide5, LIGHT_BG)
add_section_header(slide5, "智能邮件管理", "Intelligent Mail Management — AI-Powered Analysis Pipeline")

# Pipeline flow
flow_steps = [
    ("📧\n邮件入库", PRIMARY),
    ("⚙️\n分析任务\n入队", SECONDARY),
    ("🧠\nPython 插件\n分析", RGBColor(0x8E, 0x44, 0xAD)),
    ("📊\n结果入库\n标签更新", GREEN),
    ("🔔\n风险推送\n通知", ACCENT),
]

x = Inches(0.8)
for text, color in flow_steps:
    box = add_rect(slide5, x, Inches(2.0), Inches(2.2), Inches(1.2), color)
    box.text = text
    box.text_frame.paragraphs[0].font.size = Pt(14)
    box.text_frame.paragraphs[0].font.color.rgb = WHITE
    box.text_frame.paragraphs[0].font.bold = True
    box.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    box.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    # Arrow
    if x < Inches(9):
        add_textbox(slide5, x + Inches(2.2), Inches(2.3), Inches(0.5), Inches(0.5),
                    "→", font_size=28, color=PRIMARY, bold=True, alignment=PP_ALIGN.CENTER)
    x += Inches(2.65)

# Three analysis dimensions
add_textbox(slide5, Inches(0.8), Inches(3.6), Inches(4), Inches(0.4),
            "三大分析维度", font_size=22, color=DARK, bold=True)

dimensions = [
    ("垃圾邮件检测", "spam", [
        "规则引擎：URL 黑名单、短链接检测",
        "文本特征：紧急词、支付词、威胁词",
        "统计模型：朴素贝叶斯 / 逻辑回归",
        "标签：normal / spam / unknown",
    ], PRIMARY),
    ("优先级识别", "priority", [
        "关键内容：审批、故障、合同到期",
        "发件人权重与历史交互分析",
        "时间敏感度评估",
        "标签：high / normal / low",
    ], SECONDARY),
    ("风险检测", "risk", [
        "恶意链接检测（域名信誉库）",
        "钓鱼域名识别（IDN 同形异义）",
        "高危附件检测（可执行文件）",
        "等级：none → critical 五级",
    ], RGBColor(0xEF, 0x44, 0x44)),
]

for i, (title, key, details, color) in enumerate(dimensions):
    left = Inches(0.8 + i * 4.1)
    add_rect(slide5, left, Inches(4.1), Inches(3.8), Inches(2.9), WHITE)
    add_rect(slide5, left, Inches(4.1), Inches(3.8), Inches(0.55), color)
    add_textbox(slide5, left + Inches(0.2), Inches(4.15), Inches(3.4), Inches(0.45),
                title, font_size=16, color=WHITE, bold=True)
    y = Inches(4.8)
    for d in details:
        add_textbox(slide5, left + Inches(0.25), y, Inches(3.3), Inches(0.3),
                    f"• {d}", font_size=12, color=TEXT_DARK)
        y += Inches(0.32)

add_footer(slide5, 5)

# ============================================================
# SLIDE 6: 数据库设计
# ============================================================
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide6, LIGHT_BG)
add_section_header(slide6, "数据库设计", "Database Schema — MySQL 8.0 + utf8mb4")

# Left: ER overview
add_textbox(slide6, Inches(0.8), Inches(1.7), Inches(6), Inches(0.4),
            "核心数据表 (14 张)", font_size=20, color=DARK, bold=True)

tables = [
    ("用户与权限", ["sys_user", "sys_role", "sys_user_role", "login_audit"]),
    ("邮件核心", ["mail_account", "mail_folder", "mail_message", "mail_recipient"]),
    ("附件管理", ["mail_attachment"]),
    ("智能分析", ["mail_intelligence_result", "mail_threat_indicator",
                   "mail_push_event", "intelligence_plugin"]),
    ("联系人", ["contact"]),
]

y = Inches(2.2)
for group, tbls in tables:
    add_textbox(slide6, Inches(0.8), y, Inches(2.5), Inches(0.3),
                f"▎{group}", font_size=14, color=PRIMARY, bold=True)
    add_textbox(slide6, Inches(3.3), y, Inches(4), Inches(0.3),
                "  |  ".join(tbls), font_size=12, color=TEXT_DARK)
    y += Inches(0.35)

# Right: Key design points
add_textbox(slide6, Inches(7.5), Inches(1.7), Inches(5), Inches(0.4),
            "设计要点", font_size=20, color=DARK, bold=True)

design_points = [
    "主键统一 BIGINT AUTO_INCREMENT，预留雪花 ID",
    "软删除字段统一为 deleted TINYINT",
    "邮件唯一性按 account_id + message_uid",
    "收件人类型支持 to / cc / bcc",
    "附件支持 local / minio 双存储",
    "智能分析结果独立存储，支持版本回溯",
    "推送事件按用户 + 已读状态索引",
    "插件表记录版本和校验和，支持回滚",
]
y2 = Inches(2.2)
for pt in design_points:
    add_textbox(slide6, Inches(7.5), y2, Inches(5), Inches(0.3),
                f"✓ {pt}", font_size=13, color=TEXT_DARK)
    y2 += Inches(0.35)

# Bottom: Key relationships
add_rect(slide6, Inches(0.8), Inches(4.8), Inches(11.5), Inches(2.2), WHITE)
add_textbox(slide6, Inches(1.0), Inches(4.95), Inches(5), Inches(0.35),
            "核心表关系", font_size=18, color=DARK, bold=True)

relations = [
    "sys_user (1) ──→ (N) mail_account ──→ (N) mail_folder ──→ (N) mail_message",
    "mail_message (1) ──→ (N) mail_recipient  (to/cc/bcc)",
    "mail_message (1) ──→ (N) mail_attachment  (存储路径 + 校验和)",
    "mail_message (1) ──→ (1) mail_intelligence_result ──→ (N) mail_threat_indicator",
    "mail_intelligence_result ──→ (N) mail_push_event  (高优先级/高风险推送)",
    "intelligence_plugin (1) ──→ (N) mail_intelligence_result  (版本回溯)",
]
y3 = Inches(5.4)
for rel in relations:
    add_textbox(slide6, Inches(1.0), y3, Inches(11), Inches(0.25),
                f"  {rel}", font_size=12, color=TEXT_DARK)
    y3 += Inches(0.28)

add_footer(slide6, 6)

# ============================================================
# SLIDE 7: 部署架构
# ============================================================
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide7, LIGHT_BG)
add_section_header(slide7, "部署方案", "Deployment — Docker Compose + Nginx")

# Docker services grid
services = [
    ("nginx", "Nginx 1.27\nAlpine", "前端静态资源\nAPI 反向代理", "80", PRIMARY),
    ("backend", "Spring Boot\nJava 21", "REST API 服务\n业务逻辑", "8080", SECONDARY),
    ("mysql", "MySQL 8.4", "业务数据库\nutf8mb4", "3306", GREEN),
    ("redis", "Redis 7.4\nAlpine", "缓存 / Token\n黑名单", "6379", RGBColor(0xEF, 0x44, 0x44)),
    ("minio", "MinIO\nLatest", "对象存储\n附件管理", "9000\n9001", ACCENT),
    ("mailpit", "Mailpit\nv1.21", "SMTP 测试\n邮件 Web UI", "1025\n8025", RGBColor(0x8E, 0x44, 0xAD)),
]

for i, (name, tech, desc, port, color) in enumerate(services):
    left = Inches(0.6 + i * 2.1)
    card = add_rect(slide7, left, Inches(1.9), Inches(1.9), Inches(3.2), WHITE)
    # Header
    h = add_rect(slide7, left, Inches(1.9), Inches(1.9), Inches(0.65), color)
    h.text = name
    h.text_frame.paragraphs[0].font.size = Pt(16)
    h.text_frame.paragraphs[0].font.color.rgb = WHITE
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    add_textbox(slide7, left + Inches(0.1), Inches(2.7), Inches(1.7), Inches(0.6),
                tech, font_size=12, color=TEXT_DARK, alignment=PP_ALIGN.CENTER)
    add_multiline_box(slide7, left + Inches(0.1), Inches(3.3), Inches(1.7), Inches(0.8), [
        (line, 11, TEXT_GRAY, False, PP_ALIGN.CENTER) for line in desc.split('\n')
    ])
    add_textbox(slide7, left + Inches(0.1), Inches(4.3), Inches(1.7), Inches(0.4),
                f"端口: {port}", font_size=11, color=PRIMARY, bold=True, alignment=PP_ALIGN.CENTER)

# Deployment highlights
add_textbox(slide7, Inches(0.8), Inches(5.4), Inches(11), Inches(0.4),
            "部署要点", font_size=20, color=DARK, bold=True)

deploy_points = [
    "一键启动: docker compose up -d --build",
    "生产环境必须替换 JWT 密钥 (≥32 字节) 和各服务密码",
    "MySQL/Redis/MinIO 数据目录挂载到持久化磁盘",
    "Nginx 生产环境启用 HTTPS + client_max_body_size 配置",
    "智能插件按 OS 分别构建 (.so / .dll / .dylib)，CI 签名校验",
    "后端健康检查: GET /api/health",
]
y_d = Inches(5.9)
for dp in deploy_points:
    add_textbox(slide7, Inches(0.8), y_d, Inches(11.5), Inches(0.25),
                f"▸ {dp}", font_size=13, color=TEXT_DARK)
    y_d += Inches(0.28)

add_footer(slide7, 7)

# ============================================================
# SLIDE 8: 开发阶段与进度
# ============================================================
slide8 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide8, LIGHT_BG)
add_section_header(slide8, "开发阶段与进度", "Development Roadmap — 七阶段迭代")

phases = [
    ("Phase 1", "基础框架", "✅ 完成", GREEN, [
        "Vite + Spring Boot 项目初始化",
        "MySQL / Redis / MyBatis-Plus 接入",
        "统一响应 / 异常处理 / 参数校验",
        "Docker Compose 本地依赖服务",
    ]),
    ("Phase 2", "认证与权限", "✅ 完成", GREEN, [
        "用户表 / 角色表 / 登录审计表",
        "Spring Security + JWT 双 Token",
        "前端登录页 + 路由守卫",
        "Token 过期处理 + 退出登录",
    ]),
    ("Phase 3", "邮箱与发信", "✅ 完成", GREEN, [
        "邮箱账号 CRUD（多账号绑定）",
        "SMTP SSL/TLS 配置测试",
        "Jakarta Mail 发信 + 附件",
        "Mailpit 联调测试",
    ]),
    ("Phase 4", "收信与管理", "✅ 完成", GREEN, [
        "IMAP 同步邮件 + 文件夹",
        "邮件列表 / 详情 / 搜索 / 分页",
        "标记已读 / 删除 / 草稿",
        "已读/未读筛选",
    ]),
    ("Phase 5", "联系人与体验", "🔄 进行中", ACCENT, [
        "联系人 CRUD + 自动补全",
        "邮件列表筛选和分页优化",
        "附件预览 / 下载权限校验",
        "Dark Mode 主题切换",
    ]),
    ("Phase 6", "智能邮件管理", "🔄 进行中", ACCENT, [
        "Java 插件加载 + 任务编排",
        "Python 垃圾/优先级/风险检测",
        "ABI 定义 + 超时熔断",
        "前端风险标识 + 推送通知",
    ]),
    ("Phase 7", "部署与运维", "📋 规划中", RGBColor(0x6C, 0x75, 0x7D), [
        "前后端 Dockerfile + Nginx",
        "生产配置 / 日志 / 健康检查",
        "数据备份策略",
        "Python 插件 CI 构建签名",
    ]),
]

y = Inches(1.8)
for phase_num, name, status, color, items in phases:
    # Phase indicator
    ph = add_rect(slide8, Inches(0.6), y, Inches(1.0), Inches(0.65), color)
    ph.text = phase_num
    ph.text_frame.paragraphs[0].font.size = Pt(11)
    ph.text_frame.paragraphs[0].font.color.rgb = WHITE
    ph.text_frame.paragraphs[0].font.bold = True
    ph.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    ph.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Name + status
    add_textbox(slide8, Inches(1.8), y + Inches(0.02), Inches(2.5), Inches(0.3),
                name, font_size=15, color=DARK, bold=True)
    add_textbox(slide8, Inches(3.0), y + Inches(0.32), Inches(1.5), Inches(0.25),
                status, font_size=11, color=color, bold=True)

    # Items
    for j, item in enumerate(items):
        left = Inches(4.8) + Inches(j * 2.15)
        add_textbox(slide8, left, y + Inches(0.02), Inches(2.0), Inches(0.6),
                    f"• {item}", font_size=11, color=TEXT_DARK)

    y += Inches(0.78)

add_footer(slide8, 8)

# ============================================================
# SLIDE 9: 安全特性
# ============================================================
slide9 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide9, LIGHT_BG)
add_section_header(slide9, "安全特性", "Security Hardening — 纵深防御")

security_items = [
    ("认证安全", PRIMARY, [
        "JWT access + refresh 双 Token 机制",
        "BCrypt 密码哈希，杜绝硬编码密码",
        "登录限流 5次/分钟 (RateLimitFilter)",
        "登录审计日志 (IP / UA / 成功/失败)",
        "JWT Secret 启动时校验 ≥32 字节",
    ]),
    ("接口安全", SECONDARY, [
        "SecurityUtils 未认证不返回 admin 角色",
        "异常信息脱敏，不泄露错误详情",
        "显式 CORS 允许源配置",
        "参数校验 (@Valid + 统一异常处理)",
        "API 统一响应格式 ApiResponse",
    ]),
    ("数据安全", GREEN, [
        "邮箱账号密码加密存储 (auth_password_encrypted)",
        "软删除数据隔离 (deleted 字段)",
        "用户数据隔离 (user_id 级联)",
        "附件校验和完整性验证",
        "生产密码通过环境变量注入",
    ]),
    ("智能安全", ACCENT, [
        "恶意链接检测 + 域名信誉库",
        "钓鱼邮件识别 (发件人伪装检测)",
        "高危附件检测 (可执行文件等)",
        "插件超时熔断 2s (不阻塞主链路)",
        "插件版本校验和签名验证",
    ]),
]

for i, (title, color, items) in enumerate(security_items):
    left = Inches(0.6 + i * 3.15)
    add_rect(slide9, left, Inches(1.8), Inches(3.0), Inches(5.2), WHITE)
    h = add_rect(slide9, left, Inches(1.8), Inches(3.0), Inches(0.6), color)
    h.text = f"🔒 {title}"
    h.text_frame.paragraphs[0].font.size = Pt(16)
    h.text_frame.paragraphs[0].font.color.rgb = WHITE
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    y = Inches(2.6)
    for item in items:
        add_textbox(slide9, left + Inches(0.2), y, Inches(2.6), Inches(0.35),
                    f"✓ {item}", font_size=12, color=TEXT_DARK)
        y += Inches(0.42)

add_footer(slide9, 9)

# ============================================================
# SLIDE 10: 技术亮点
# ============================================================
slide10 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide10, LIGHT_BG)
add_section_header(slide10, "技术亮点", "Technical Highlights")

highlights = [
    ("插件化 AI 引擎", [
        "Python 原生动态库 (.so/.dll)，与 Java 后端解耦",
        "稳定 ABI: analyze_email_json(json) → json",
        "支持热替换模型，版本可回溯",
        "超时熔断降级，保障邮件主链路可用",
    ], PRIMARY),
    ("真正的邮件收发", [
        "Jakarta Mail 实现 SMTP 发信 + IMAP 收信",
        "SSL/TLS 全兼容 Gmail/QQ/Outlook/163 等",
        "附件上传下载 + 校验和完整性验证",
        "邮件文件夹同步 + 未读计数",
    ], SECONDARY),
    ("多租户数据隔离", [
        "邮箱账号按 user_id 隔离",
        "邮件/联系人/附件全部按用户隔离",
        "同一邮箱地址可供不同用户绑定",
        "软删除 + deleted 字段设计",
    ], GREEN),
    ("安全纵深防御", [
        "从 JWT 认证 → API 限流 → 异常脱敏 → CORS → 数据加密",
        "修复多项安全漏洞（硬编码密码、错误详情泄露等）",
        "登录审计全链路追踪",
        "生产环境密钥注入机制",
    ], ACCENT),
    ("生产级部署", [
        "Docker Compose 一键启动 7 个服务",
        "Nginx 反向代理 + 静态资源",
        "健康检查 + depends_on 依赖编排",
        "MinIO 对象存储，支持 local/minio 切换",
    ], RGBColor(0x8E, 0x44, 0xAD)),
]

for i, (title, items, color) in enumerate(highlights):
    if i < 3:
        left = Inches(0.6 + i * 4.2)
        top = Inches(1.8)
    else:
        left = Inches(0.6 + (i - 3) * 6.3)
        top = Inches(4.5)

    add_rect(slide10, left, top, Inches(3.9), Inches(2.4), WHITE)
    h = add_rect(slide10, left, top, Inches(3.9), Inches(0.55), color)
    h.text = title
    h.text_frame.paragraphs[0].font.size = Pt(16)
    h.text_frame.paragraphs[0].font.color.rgb = WHITE
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    y_item = top + Inches(0.7)
    for item in items:
        add_textbox(slide10, left + Inches(0.2), y_item, Inches(3.5), Inches(0.3),
                    f"▸ {item}", font_size=12, color=TEXT_DARK)
        y_item += Inches(0.32)

add_footer(slide10, 10)

# ============================================================
# SLIDE 11: 代码统计
# ============================================================
slide11 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide11, LIGHT_BG)
add_section_header(slide11, "项目数据", "Project Statistics")

# Get stats from git
import subprocess
os.chdir('/home/x12w/projects/email-system')

# Count files
backend_java = subprocess.getoutput("find backend/src -name '*.java' -type f | wc -l").strip()
frontend_files = subprocess.getoutput("find frontend/src -type f -not -path '*/.gitkeep' | wc -l").strip()
total_commits = subprocess.getoutput("git rev-list --count HEAD").strip()
doc_files = subprocess.getoutput("find docs -name '*.md' -type f | wc -l").strip()

# Stats cards
stats = [
    (f"{backend_java}", "Java 后端类", PRIMARY),
    (f"{frontend_files}", "前端源文件", SECONDARY),
    (f"{total_commits}", "Git 提交", GREEN),
    (f"{doc_files}", "设计文档", ACCENT),
]

for i, (num, label, color) in enumerate(stats):
    left = Inches(0.8 + i * 3.1)
    add_rect(slide11, left, Inches(2.0), Inches(2.7), Inches(1.8), WHITE)
    add_textbox(slide11, left + Inches(0.3), Inches(2.2), Inches(2.1), Inches(0.9),
                num, font_size=48, color=color, bold=True, alignment=PP_ALIGN.CENTER)
    add_textbox(slide11, left + Inches(0.3), Inches(3.1), Inches(2.1), Inches(0.4),
                label, font_size=16, color=TEXT_GRAY, alignment=PP_ALIGN.CENTER)

# Tech stack summary
add_textbox(slide11, Inches(0.8), Inches(4.2), Inches(11), Inches(0.4),
            "技术栈总览", font_size=20, color=DARK, bold=True)

tech_rows = [
    ("前端", "Vue 3, TypeScript, Vite, Pinia, Vue Router, Element Plus, Axios"),
    ("后端", "Spring Boot, Spring Security, JWT, MyBatis-Plus, Jakarta Mail, Flyway"),
    ("数据", "MySQL 8.0, Redis 7, MinIO Object Storage"),
    ("AI", "Python, scikit-learn/ONNX, JNA/JNI Native Plugin"),
    ("测试", "Mailpit (SMTP), JUnit, pytest"),
    ("部署", "Docker, Docker Compose, Nginx, CI/CD"),
]

y_t = Inches(4.7)
for label, techs in tech_rows:
    add_textbox(slide11, Inches(0.8), y_t, Inches(1.5), Inches(0.3),
                label, font_size=14, color=PRIMARY, bold=True)
    add_textbox(slide11, Inches(2.3), y_t, Inches(10), Inches(0.3),
                techs, font_size=13, color=TEXT_DARK)
    y_t += Inches(0.36)

add_footer(slide11, 11)

# ============================================================
# SLIDE 12: 总结与展望
# ============================================================
slide12 = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide12, DARK)
add_rect(slide12, Inches(0), Inches(0), prs.slide_width, Inches(0.12), PRIMARY)
add_rect(slide12, Inches(0), Inches(7.38), prs.slide_width, Inches(0.12), PRIMARY)

add_textbox(slide12, Inches(1.0), Inches(0.6), Inches(11), Inches(0.8),
            "总结与展望", font_size=40, color=WHITE, bold=True)

# Summary
add_textbox(slide12, Inches(1.0), Inches(1.6), Inches(5.5), Inches(0.4),
            "🎯 项目成果", font_size=22, color=ACCENT, bold=True)

summary_points = [
    "完成从零到一的全栈邮件系统搭建",
    "实现 SMTP/IMAP 真正的邮件收发闭环",
    "集成 AI 智能分析管线（垃圾检测 + 优先级 + 风险）",
    "建立安全纵深防御体系（认证 / 限流 / 脱敏 / 加密）",
    "14 张数据表完整设计，支持多租户隔离",
    "Docker Compose 一键部署，开发体验友好",
]
y_s = Inches(2.2)
for sp in summary_points:
    add_textbox(slide12, Inches(1.0), y_s, Inches(5.5), Inches(0.3),
                f"✓ {sp}", font_size=14, color=RGBColor(0xCC, 0xCC, 0xCC))
    y_s += Inches(0.38)

# Future
add_textbox(slide12, Inches(7.0), Inches(1.6), Inches(5.5), Inches(0.4),
            "🚀 未来规划", font_size=22, color=SECONDARY, bold=True)

future_points = [
    "Python 插件升级为深度学习模型 (ONNX)",
    "WebSocket 实时推送 + 桌面通知",
    "邮件全文搜索引擎 (Elasticsearch)",
    "多语言国际化和无障碍访问",
    "Kubernetes Helm Chart 部署支持",
    "邮件规则引擎 + 自动归档分类",
    "多因素认证 (MFA) 集成",
    "性能压测与大规模邮箱并发优化",
]
y_f = Inches(2.2)
for fp in future_points:
    add_textbox(slide12, Inches(7.0), y_f, Inches(5.5), Inches(0.3),
                f"→ {fp}", font_size=14, color=RGBColor(0xCC, 0xCC, 0xCC))
    y_f += Inches(0.38)

# Bottom
add_textbox(slide12, Inches(1.0), Inches(6.0), Inches(11), Inches(0.5),
            "感谢聆听  ·  欢迎交流", font_size=24, color=WHITE, bold=True,
            alignment=PP_ALIGN.CENTER)
add_textbox(slide12, Inches(1.0), Inches(6.5), Inches(11), Inches(0.4),
            "Email System — 智能邮件管理平台", font_size=14, color=TEXT_GRAY,
            alignment=PP_ALIGN.CENTER)

add_footer(slide12, 12)

# ============================================================
# Save
# ============================================================
output_path = '/home/x12w/projects/email-system/docs/Email-System-项目汇报.pptx'
prs.save(output_path)
print(f"PPT saved to: {output_path}")
print(f"Total slides: {len(prs.slides)}")
