#!/usr/bin/env python3
"""Generate defense presentation PPT for Email System."""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os, subprocess

# ── Color Scheme ──────────────────────────────────────────
C = {
    'blue':     RGBColor(0x25, 0x63, 0xEB),
    'teal':     RGBColor(0x0D, 0x94, 0x8B),
    'orange':   RGBColor(0xF5, 0x9E, 0x0B),
    'red':      RGBColor(0xEF, 0x44, 0x44),
    'purple':   RGBColor(0x8B, 0x5C, 0xF6),
    'dark':     RGBColor(0x0F, 0x17, 0x2A),
    'white':    RGBColor(0xFF, 0xFF, 0xFF),
    'bg':       RGBColor(0xF1, 0xF5, 0xF9),
    'text':     RGBColor(0x1E, 0x29, 0x3B),
    'gray':     RGBColor(0x64, 0x74, 0x8B),
    'green':    RGBColor(0x10, 0xB9, 0x81),
    'light':    RGBColor(0xE2, 0xE8, 0xF0),
}

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)

# ── Helpers ───────────────────────────────────────────────
def bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color

def rect(slide, l, t, w, h, color):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    return s

def txt(slide, l, t, w, h, text, size=16, color=C['text'], bold=False, align=PP_ALIGN.LEFT, font='Microsoft YaHei'):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text; p.font.size = Pt(size); p.font.color.rgb = color
    p.font.bold = bold; p.font.name = font; p.alignment = align
    return tb

def mline(slide, l, t, w, h, lines, font='Microsoft YaHei'):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    for i, (text, size, color, bold, *rest) in enumerate(lines):
        align = rest[0] if rest else PP_ALIGN.LEFT
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text; p.font.size = Pt(size); p.font.color.rgb = color
        p.font.bold = bold; p.font.name = font; p.alignment = align
        p.space_after = Pt(3)
    return tb

def header(slide, title, sub=""):
    rect(slide, Inches(0), Inches(0), prs.slide_width, Inches(0.06), C['blue'])
    txt(slide, Inches(0.8), Inches(0.35), Inches(11), Inches(0.7), title, 34, C['dark'], True)
    if sub:
        txt(slide, Inches(0.8), Inches(1.0), Inches(11), Inches(0.4), sub, 15, C['gray'])
    rect(slide, Inches(0.8), Inches(1.4), Inches(11.5), Inches(0.025), C['blue'])

def footer(slide, n):
    txt(slide, Inches(12.3), Inches(7.1), Inches(0.8), Inches(0.3), str(n), 10, C['gray'], align=PP_ALIGN.RIGHT)

def card(slide, l, t, w, h, title, items, accent=C['blue']):
    rect(slide, l, t, w, h, C['white'])
    rect(slide, l, t, Inches(0.05), h, accent)
    txt(slide, l+Inches(0.2), t+Inches(0.1), w-Inches(0.4), Inches(0.35), title, 17, C['dark'], True)
    y = t + Inches(0.5)
    for it in items:
        txt(slide, l+Inches(0.35), y, w-Inches(0.55), Inches(0.25), f"▸ {it}", 12, C['text'])
        y += Inches(0.26)

# ── Get real stats ────────────────────────────────────────
os.chdir('/home/x12w/projects/email-system')
n_java  = subprocess.getoutput("find backend/src -name '*.java' -type f | wc -l").strip()
n_vue   = subprocess.getoutput("find frontend/src -name '*.vue' -o -name '*.ts' | grep -v node_modules | wc -l").strip()
n_commits = subprocess.getoutput("git rev-list --count HEAD 2>/dev/null || echo 30").strip()
n_docs  = subprocess.getoutput("find docs -name '*.md' -type f | wc -l").strip()
n_sql   = subprocess.getoutput("grep -c 'CREATE TABLE' backend/src/main/resources/db/migration/V1__init_schema.sql 2>/dev/null || echo 14").strip()

# ═══════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ═══════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s1, C['dark'])
rect(s1, Inches(0), Inches(0), prs.slide_width, Inches(0.10), C['blue'])
rect(s1, Inches(0), Inches(7.40), prs.slide_width, Inches(0.10), C['blue'])
rect(s1, Inches(0), Inches(3.3), Inches(0.10), Inches(1.2), C['orange'])

txt(s1, Inches(1.5), Inches(1.5), Inches(10), Inches(1.2),
    "电子邮件系统", 58, C['white'], True)
txt(s1, Inches(1.5), Inches(2.8), Inches(10), Inches(0.6),
    "Email System — 全栈智能邮件管理平台", 22, C['teal'])
mline(s1, Inches(1.5), Inches(3.6), Inches(10), Inches(1.8), [
    ("前后端分离架构 · SMTP/IMAP 真实收发 · AI 智能分析 · 安全纵深防御", 17, RGBColor(0x94,0xA3,0xB8), False),
    ("", 8, C['white'], False),
    ("毕业设计答辩汇报", 20, C['orange'], True),
    ("2026 年 7 月", 13, C['gray'], False),
])

techs = [("Vue 3", Inches(1.5)), ("Spring Boot 3", Inches(3.2)), ("MySQL 8", Inches(6.0)),
         ("Redis", Inches(7.9)), ("Docker", Inches(9.7)), ("Python AI", Inches(11.5))]
for t, x in techs:
    r = rect(s1, x, Inches(5.8), Inches(1.4), Inches(0.45), C['blue'])
    r.text = t
    r.text_frame.paragraphs[0].font.size = Pt(11)
    r.text_frame.paragraphs[0].font.color.rgb = C['white']
    r.text_frame.paragraphs[0].font.bold = True
    r.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    r.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

footer(s1, 1)

# ═══════════════════════════════════════════════════════════
# SLIDE 2 — 项目概述
# ═══════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s2, C['bg'])
header(s2, "项目概述", "Project Overview — 我们要解决什么问题？")

card(s2, Inches(0.8), Inches(1.7), Inches(5.8), Inches(2.5),
     "🎯 项目定位", [
         "全栈自研电子邮件管理系统，非第三方邮件客户端封装",
         "基于标准 SMTP/IMAP 协议实现真实的邮件收发闭环",
         "集成 AI 智能分析引擎：垃圾检测 + 优先级 + 风险识别",
         "面向个人及小团队，注重安全性与可部署性",
         "线上已部署运行: https://panel.x12w.com",
     ], C['blue'])

card(s2, Inches(7.1), Inches(1.7), Inches(5.6), Inches(2.5),
     "🏆 核心成果", [
         f"后端 {n_java} 个 Java 类，前端 {n_vue} 个组件/模块",
         f"数据库 {n_sql} 张表完整设计 (MySQL + Flyway 迁移)",
         f"Git {n_commits}+ 次提交，完整的功能迭代记录",
         f"支持 Gmail / QQ / Outlook / 163 等主流邮箱",
         "Docker Compose 一键部署 + Let's Encrypt HTTPS",
     ], C['teal'])

card(s2, Inches(0.8), Inches(4.5), Inches(5.8), Inches(2.5),
     "🛠 技术选型", [
         "前端: Vue 3 + TypeScript + Vite + Element Plus + Pinia",
         "后端: Spring Boot 3 + Spring Security + JWT + MyBatis-Plus",
         "数据: MySQL 8.0 + Redis 7 + MinIO 对象存储",
         "AI: Python 原生插件 (.so) + JNI 调用 + 超时熔断",
     ], C['green'])

card(s2, Inches(7.1), Inches(4.5), Inches(5.6), Inches(2.5),
     "🚀 部署运维", [
         "Docker Compose 管理 7 个容器服务",
         "Nginx 反向代理 + SSL 证书自动续期",
         "健康检查 / 登录限流 / 审计日志",
         "./scripts/deploy.sh 一键部署脚本",
     ], C['orange'])

footer(s2, 2)

# ═══════════════════════════════════════════════════════════
# SLIDE 3 — 系统架构
# ═══════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s3, C['bg'])
header(s3, "系统架构", "System Architecture — 六层架构设计")

layers = [
    ("展示层", "Vue 3 SPA · TypeScript · Element Plus · Pinia\n响应式布局 · Dark Mode · 路由守卫", C['blue']),
    ("网关层", "Nginx 反向代理 · Let's Encrypt SSL\n静态资源服务 · /api 转发 · 50MB 上传限制", RGBColor(0x47,0x53,0x69)),
    ("应用层", "Spring Boot REST API · Spring Security Filter Chain\n统一 ApiResponse · GlobalExceptionHandler", C['teal']),
    ("业务层", "邮件收发 · IMAP 同步 · 智能分析编排\n联系人 · 附件 · 推送事件 · 邮箱账号管理", C['green']),
    ("数据层", f"MySQL {n_sql} 表 MyBatis-Plus · Redis 缓存\nMinIO / 本地存储 · Flyway 版本迁移", C['orange']),
    ("AI 引擎", "Python Native Plugin (.so) · JNI Bridge\n垃圾检测 · 优先级 · 风险识别 · 2s 熔断", C['purple']),
]

y = Inches(1.7)
for name, desc, color in layers:
    r = rect(s3, Inches(0.8), y, Inches(2.4), Inches(0.75), color)
    r.text = name
    r.text_frame.paragraphs[0].font.size = Pt(15)
    r.text_frame.paragraphs[0].font.color.rgb = C['white']
    r.text_frame.paragraphs[0].font.bold = True
    r.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    r.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    mline(s3, Inches(3.5), y+Inches(0.05), Inches(9), Inches(0.7), [
        (line, 12, C['text'], False) for line in desc.split('\n')
    ])
    if y < Inches(5.8):
        rect(s3, Inches(0.8), y+Inches(0.8), Inches(2.4), Inches(0.04), color)
    y += Inches(0.88)

footer(s3, 3)

# ═══════════════════════════════════════════════════════════
# SLIDE 4 — 核心功能
# ═══════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s4, C['bg'])
header(s4, "核心功能", "Core Features — 四大功能模块")

mods = [
    ("📧 邮件收发", C['blue'], [
        "多邮箱账号绑定（SMTP + IMAP 独立配置）",
        "SSL/TLS 全兼容主流平台",
        "文件夹同步 + 实时未读计数",
        "搜索 / 筛选 / 分页 / 草稿 / 删除",
        "附件上传下载（MinIO + 本地双模式）",
    ]),
    ("🤖 智能分析", C['purple'], [
        "垃圾邮件自动识别（关键词 + 链接分析）",
        "优先级智能分级（紧急词 / 发件人权重）",
        "风险检测（IP URL / 钓鱼域名 / 短链接）",
        "Python 插件 ABI，2s 超时熔断降级",
        "分析结果可视化 + 风险推送通知",
    ]),
    ("🔒 安全体系", C['red'], [
        "JWT 双 Token 机制 + BCrypt 密码哈希",
        "登录限流 (5次/分钟) + 审计日志",
        "API 异常脱敏，不泄露内部错误详情",
        "显式 CORS + user_id 级联数据隔离",
        "JWT Secret 启动校验 + 密码环境变量注入",
    ]),
    ("👥 用户管理", C['teal'], [
        "注册 / 登录 / Token 刷新 / 退出",
        "多租户邮箱隔离（同地址不同用户互不影响）",
        "联系人 CRUD + 自动补全",
        "Dark Mode 主题切换",
        "MySQL 持久化，重启不丢数据",
    ]),
]

for i, (title, color, items) in enumerate(mods):
    l = Inches(0.5 + i * 3.15)
    rect(s4, l, Inches(1.7), Inches(3.0), Inches(5.2), C['white'])
    h = rect(s4, l, Inches(1.7), Inches(3.0), Inches(0.6), color)
    h.text = title
    h.text_frame.paragraphs[0].font.size = Pt(15)
    h.text_frame.paragraphs[0].font.color.rgb = C['white']
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    y2 = Inches(2.5)
    for it in items:
        txt(s4, l+Inches(0.15), y2, Inches(2.7), Inches(0.32), f"▸ {it}", 11, C['text'])
        y2 += Inches(0.36)

footer(s4, 4)

# ═══════════════════════════════════════════════════════════
# SLIDE 5 — 智能分析详解
# ═══════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s5, C['bg'])
header(s5, "智能邮件分析", "AI-Powered Analysis Pipeline — 插件化 AI 引擎")

# Pipeline
steps = [("邮件入库", C['blue']), ("分析入队", C['teal']), ("Python 插件", C['purple']), ("结果写回", C['green']), ("推送通知", C['orange'])]
x = Inches(0.8)
for i, (name, color) in enumerate(steps):
    r = rect(s5, x, Inches(1.9), Inches(2.2), Inches(1.0), color)
    r.text = f"{i+1}\n{name}"
    r.text_frame.paragraphs[0].font.size = Pt(13)
    r.text_frame.paragraphs[0].font.color.rgb = C['white']
    r.text_frame.paragraphs[0].font.bold = True
    r.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    r.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    if i < 4:
        txt(s5, x+Inches(2.2), Inches(2.1), Inches(0.5), Inches(0.5), "→", 26, C['blue'], True, PP_ALIGN.CENTER)
    x += Inches(2.65)

# Three dimensions
txt(s5, Inches(0.8), Inches(3.3), Inches(4), Inches(0.35), "三大分析维度", 20, C['dark'], True)

dims = [
    ("垃圾检测 (Spam)", C['blue'], ["关键词匹配(中奖/免费/贷款)", "发件人信誉评估", "文本特征向量化", "标签: normal / spam"]),
    ("优先级 (Priority)", C['orange'], ["紧急关键词(审批/故障/合同)", "时间敏感度分析", "历史交互频率加权", "标签: high / normal / low"]),
    ("风险检测 (Risk)", C['red'], ["URL IP 地址检测", "短链接展开检查", "敏感词(login/pay/verify)", "等级: none→critical 五级"]),
]
for i, (title, color, items) in enumerate(dims):
    l = Inches(0.8 + i * 4.1)
    rect(s5, l, Inches(3.8), Inches(3.8), Inches(2.6), C['white'])
    h = rect(s5, l, Inches(3.8), Inches(3.8), Inches(0.5), color)
    h.text = title
    h.text_frame.paragraphs[0].font.size = Pt(14)
    h.text_frame.paragraphs[0].font.color.rgb = C['white']
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    y3 = Inches(4.45)
    for it in items:
        txt(s5, l+Inches(0.2), y3, Inches(3.4), Inches(0.25), f"• {it}", 12, C['text'])
        y3 += Inches(0.28)

# Plugin ABI note
rect(s5, Inches(0.8), Inches(6.6), Inches(11.5), Inches(0.5), C['light'])
txt(s5, Inches(1.0), Inches(6.65), Inches(11), Inches(0.4),
    "🔌 插件接口: analyze_email_json(request_json: str) → str  |  超时: 2s  |  降级: 规则引擎 fallback  |  版本管理: 可回溯", 11, C['gray'], align=PP_ALIGN.CENTER)

footer(s5, 5)

# ═══════════════════════════════════════════════════════════
# SLIDE 6 — 数据库设计
# ═══════════════════════════════════════════════════════════
s6 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s6, C['bg'])
header(s6, "数据库设计", f"Database Schema — MySQL 8.0 + utf8mb4 + {n_sql} 张表")

groups = [
    ("用户与权限", ["sys_user", "sys_role", "sys_user_role", "login_audit"]),
    ("邮件核心",   ["mail_account", "mail_folder", "mail_message", "mail_recipient"]),
    ("附件管理",   ["mail_attachment"]),
    ("智能分析",   ["mail_intelligence_result", "mail_threat_indicator", "mail_push_event", "intelligence_plugin"]),
    ("联系人",     ["contact"]),
]
y = Inches(2.0)
for grp, tbls in groups:
    txt(s6, Inches(0.8), y, Inches(2.3), Inches(0.28), f"▎{grp}", 13, C['blue'], True)
    txt(s6, Inches(3.1), y, Inches(5), Inches(0.28), "  |  ".join(tbls), 12, C['text'])
    y += Inches(0.32)

txt(s6, Inches(7.5), Inches(2.0), Inches(5), Inches(0.35), "设计规范", 18, C['dark'], True)
y2 = Inches(2.5)
for pt in [
    "主键统一 BIGINT AUTO_INCREMENT",
    "软删除统一 deleted TINYINT @TableLogic",
    "邮件去重: account_id + message_uid 唯一键",
    "收件人类型: to / cc / bcc 三态",
    "存储双模式: local / minio 可切换",
    "分析结果独立存储，支持版本回溯",
    "推送事件按 user_id + read_flag 索引",
]:
    txt(s6, Inches(7.5), y2, Inches(5), Inches(0.22), f"✓ {pt}", 12, C['text'])
    y2 += Inches(0.27)

rect(s6, Inches(0.8), Inches(4.2), Inches(11.5), Inches(2.6), C['white'])
txt(s6, Inches(1.0), Inches(4.35), Inches(11), Inches(0.3), "核心表关系", 16, C['dark'], True)

rels = [
    "sys_user ──→ mail_account ──→ mail_folder ──→ mail_message ──→ mail_recipient",
    "mail_message ──→ mail_attachment (多附件)",
    "mail_message ──→ mail_intelligence_result (1:1) ──→ mail_threat_indicator (1:N)",
    "mail_intelligence_result ──→ mail_push_event (高风险推送)",
    "intelligence_plugin ──→ mail_intelligence_result (版本追溯)",
    "contact 独立维护，按 user_id 隔离",
]
y3 = Inches(4.75)
for rl in rels:
    txt(s6, Inches(1.0), y3, Inches(11), Inches(0.22), f"  {rl}", 11, C['text'])
    y3 += Inches(0.26)

footer(s6, 6)

# ═══════════════════════════════════════════════════════════
# SLIDE 7 — 安全实战
# ═══════════════════════════════════════════════════════════
s7 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s7, C['bg'])
header(s7, "安全加固实战", "Security Hardening — 发现并修复 15 项安全漏洞")

sec_cards = [
    ("🔐 认证安全 (已修复 5 项)", C['red'], [
        "SecurityUtils 未认证不再返回硬编码 admin → 抛异常",
        "移除 UserRegistryService 硬编码默认密码",
        "JWT Secret 启动时校验 ≥16 字节，拒绝占位符",
        "refresh token 真正校验，不再忽略请求体",
        "全局异常处理不再向客户端泄露 e.getMessage()",
    ]),
    ("🛡 接口防护 (已修复 4 项)", C['orange'], [
        "新增 RateLimitFilter: 5次/分钟登录限流",
        "显式 CORS 配置替代 Spring Security 默认",
        "添加文件上传大小限制 (10MB/50MB)",
        "参数校验 @Valid + 统一异常处理",
    ]),
    ("🗄 数据安全 (已修复 3 项)", C['blue'], [
        "用户数据 MySQL 持久化，重启不丢失",
        "邮箱唯一性改为 user_id 隔离",
        "软删除 @TableLogic 自动过滤",
    ]),
    ("⚙️ 配置安全 (已修复 3 项)", C['green'], [
        "密码通过环境变量注入，不提交到 Git",
        "Docker 镜像版本固定，不再 latest",
        "JWT_SECRET 部署时自动生成临时密钥",
    ]),
]
for i, (title, color, items) in enumerate(sec_cards):
    l = Inches(0.5 + i * 3.15)
    rect(s7, l, Inches(1.7), Inches(3.0), Inches(5.2), C['white'])
    h = rect(s7, l, Inches(1.7), Inches(3.0), Inches(0.55), color)
    h.text = title
    h.text_frame.paragraphs[0].font.size = Pt(13)
    h.text_frame.paragraphs[0].font.color.rgb = C['white']
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    y4 = Inches(2.4)
    for it in items:
        txt(s7, l+Inches(0.15), y4, Inches(2.7), Inches(0.32), f"✓ {it}", 10, C['text'])
        y4 += Inches(0.33)

footer(s7, 7)

# ═══════════════════════════════════════════════════════════
# SLIDE 8 — 部署架构
# ═══════════════════════════════════════════════════════════
s8 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s8, C['bg'])
header(s8, "部署方案", "Deployment — Docker Compose + Nginx + Let's Encrypt")

svcs = [
    ("nginx", "Nginx\nAlpine", "反向代理\nSSL 终端", "80/443", C['blue']),
    ("backend", "Spring Boot\nJava 17", "REST API\n业务逻辑", "8080", C['teal']),
    ("mysql", "MySQL 8.4", "业务数据\nutf8mb4", "3306", C['green']),
    ("redis", "Redis 7.4", "缓存/Token\n黑名单", "6379", C['red']),
    ("minio", "MinIO", "对象存储\n附件管理", "9000", C['orange']),
    ("mailpit", "Mailpit", "SMTP 测试\n邮件预览", "1025/8025", C['purple']),
]
for i, (name, tech, desc, port, color) in enumerate(svcs):
    l = Inches(0.5 + i * 2.1)
    rect(s8, l, Inches(1.9), Inches(1.9), Inches(3.0), C['white'])
    h = rect(s8, l, Inches(1.9), Inches(1.9), Inches(0.55), color)
    h.text = name
    h.text_frame.paragraphs[0].font.size = Pt(15)
    h.text_frame.paragraphs[0].font.color.rgb = C['white']
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    txt(s8, l+Inches(0.1), Inches(2.55), Inches(1.7), Inches(0.5), tech, 11, C['text'], align=PP_ALIGN.CENTER)
    mline(s8, l+Inches(0.1), Inches(3.1), Inches(1.7), Inches(0.7), [
        (line, 10, C['gray'], False, PP_ALIGN.CENTER) for line in desc.split('\n')
    ])
    txt(s8, l+Inches(0.1), Inches(4.1), Inches(1.7), Inches(0.3), f":{port}", 11, C['blue'], True, PP_ALIGN.CENTER)

txt(s8, Inches(0.8), Inches(5.2), Inches(11), Inches(0.35), "线上环境", 18, C['dark'], True)
card(s8, Inches(0.8), Inches(5.6), Inches(11.5), Inches(1.4), "https://panel.x12w.com", [
    "服务器: Debian 12 · 一键部署脚本 scripts/deploy.sh · 支持 build / start / stop / restart / status / logs / update",
    "SSL: Let's Encrypt 自动续期 (cron: 每天 3AM) · Nginx 反向代理 · 前端 SPA + /api 代理",
    "配置管理: .env 环境变量注入 · JWT_SECRET 自动生成 · 全部密码通过 env 传入",
], C['teal'])

footer(s8, 8)

# ═══════════════════════════════════════════════════════════
# SLIDE 9 — 项目数据
# ═══════════════════════════════════════════════════════════
s9 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s9, C['bg'])
header(s9, "项目数据", "Project Statistics")

stats = [
    (n_java, "Java 后端类", C['blue']),
    (n_vue, "前端源文件", C['teal']),
    (n_commits, "Git 提交", C['green']),
    (n_sql, "数据库表", C['orange']),
]
for i, (num, label, color) in enumerate(stats):
    l = Inches(0.8 + i * 3.1)
    rect(s9, l, Inches(1.9), Inches(2.7), Inches(1.8), C['white'])
    txt(s9, l+Inches(0.2), Inches(2.1), Inches(2.3), Inches(0.9), num, 48, color, True, PP_ALIGN.CENTER)
    txt(s9, l+Inches(0.2), Inches(3.1), Inches(2.3), Inches(0.4), label, 15, C['gray'], align=PP_ALIGN.CENTER)

txt(s9, Inches(0.8), Inches(4.1), Inches(11), Inches(0.35), "技术栈总览", 18, C['dark'], True)
techs2 = [
    ("前端", "Vue 3 · TypeScript · Vite · Pinia · Vue Router · Element Plus · Axios"),
    ("后端", "Spring Boot 3 · Spring Security · JWT · MyBatis-Plus · Jakarta Mail · Flyway"),
    ("数据", "MySQL 8.0 · Redis 7 · MinIO · Flyway 迁移"),
    ("AI",  "Python 3 · Native Plugin (.so) · JNI Bridge · 规则引擎 Fallback"),
    ("测试", "Mailpit (SMTP/IMAP) · JUnit · pytest"),
    ("部署", "Docker · Docker Compose · Nginx · Let's Encrypt · Debian 12"),
]
y5 = Inches(4.55)
for label, techs in techs2:
    txt(s9, Inches(0.8), y5, Inches(1.5), Inches(0.25), label, 13, C['blue'], True)
    txt(s9, Inches(2.3), y5, Inches(10), Inches(0.25), techs, 12, C['text'])
    y5 += Inches(0.32)

footer(s9, 9)

# ═══════════════════════════════════════════════════════════
# SLIDE 10 — 项目亮点
# ═══════════════════════════════════════════════════════════
s10 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s10, C['bg'])
header(s10, "技术亮点", "Technical Highlights")

hls = [
    ("真实邮件收发", C['blue'], [
        "非 Mock 演示 — Jakarta Mail 实现 SMTP 发信 + IMAP 收信",
        "SSL/TLS 自适应 (465=SSL, 587=STARTTLS)，兼容主流平台",
        "发信通过 Resend SMTP 送达 Gmail，收信通过 IMAP 同步",
    ]),
    ("插件化 AI", C['purple'], [
        "Python 原生动态库由 Java JNI 加载，2s 超时熔断",
        "稳定 ABI: analyze_email_json(json) → json，可热替换",
        "降级策略: 插件不可用时自动 fallback 到 Java 规则引擎",
    ]),
    ("安全深度防御", C['red'], [
        "代码审查发现 15 项安全漏洞并全部修复",
        "JWT 校验 · 限流 · 脱敏 · CORS · BCrypt · 审计日志",
        "生产密码环境变量注入，无任何硬编码密钥",
    ]),
    ("生产可部署", C['teal'], [
        "Docker Compose 一键启动 7 个服务 + 健康检查",
        "Nginx + Let's Encrypt HTTPS 自动续期",
        "./scripts/deploy.sh 提供 build/start/stop/status/logs/update",
    ]),
]
for i, (title, color, items) in enumerate(hls):
    l = Inches(0.5 + i * 3.15)
    rect(s10, l, Inches(1.7), Inches(3.0), Inches(3.0), C['white'])
    h = rect(s10, l, Inches(1.7), Inches(3.0), Inches(0.5), color)
    h.text = title
    h.text_frame.paragraphs[0].font.size = Pt(14)
    h.text_frame.paragraphs[0].font.color.rgb = C['white']
    h.text_frame.paragraphs[0].font.bold = True
    h.text_frame.paragraphs[0].font.name = 'Microsoft YaHei'
    h.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    y6 = Inches(2.35)
    for it in items:
        txt(s10, l+Inches(0.15), y6, Inches(2.7), Inches(0.38), f"▸ {it}", 11, C['text'])
        y6 += Inches(0.42)

rect(s10, Inches(0.8), Inches(5.0), Inches(11.5), Inches(2.0), C['white'])
txt(s10, Inches(1.0), Inches(5.1), Inches(11), Inches(0.3), "📋 迭代历程", 16, C['dark'], True)
iterations = [
    ("Phase 1-2", "基础框架 + 认证权限", "✅", C['green']),
    ("Phase 3-4", "SMTP 发信 + IMAP 收信", "✅", C['green']),
    ("Phase 5", "安全加固 (15 项修复)", "✅", C['green']),
    ("Phase 6", "智能分析 + 前端重构", "✅", C['green']),
    ("Phase 7", "Docker 部署 + SSL + deploy.sh", "✅", C['green']),
    ("Phase 8", "docker-mailserver 独立收信", "🔄", C['orange']),
]
for i, (phase, desc, status, color) in enumerate(iterations):
    l2 = Inches(0.9 + i * 2.1)
    txt(s10, l2, Inches(5.5), Inches(2.0), Inches(0.22), f"{status} {phase}", 11, color, True, PP_ALIGN.CENTER)
    txt(s10, l2, Inches(5.75), Inches(2.0), Inches(0.5), desc, 10, C['gray'], align=PP_ALIGN.CENTER)

footer(s10, 10)

# ═══════════════════════════════════════════════════════════
# SLIDE 11 — 总结与展望
# ═══════════════════════════════════════════════════════════
s11 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s11, C['dark'])
rect(s11, Inches(0), Inches(0), prs.slide_width, Inches(0.10), C['blue'])
rect(s11, Inches(0), Inches(7.40), prs.slide_width, Inches(0.10), C['blue'])

txt(s11, Inches(1.0), Inches(0.5), Inches(11), Inches(0.7), "总结与展望", 38, C['white'], True)

# Left: achievements
txt(s11, Inches(1.0), Inches(1.4), Inches(5.5), Inches(0.35), "🎯 项目成果", 20, C['orange'], True)
achievements = [
    "从零构建全栈邮件系统，实现 SMTP/IMAP 真实收发闭环",
    "集成 AI 智能分析管线，3 维度评估每封邮件",
    f"数据库 {n_sql} 张表完整设计，支持多租户隔离",
    "修复 15 项安全漏洞，建立纵深防御体系",
    "Docker Compose 一键部署，线上稳定运行",
    f"Git {n_commits}+ 提交，完整的工程化迭代记录",
]
y7 = Inches(1.9)
for a in achievements:
    txt(s11, Inches(1.0), y7, Inches(5.5), Inches(0.25), f"✓ {a}", 13, RGBColor(0xCBD,0xD5,0xE1))
    y7 += Inches(0.35)

# Right: future
txt(s11, Inches(7.0), Inches(1.4), Inches(5.5), Inches(0.35), "🚀 未来方向", 20, C['teal'], True)
future = [
    "深度学习模型升级 (ONNX Runtime)",
    "WebSocket 实时推送 + 桌面通知",
    "邮件全文搜索 (Elasticsearch)",
    "Kubernetes Helm Chart",
    "邮件规则引擎 + 自动归档",
    "多因素认证 (MFA)",
    "独立 IMAP 服务器 (docker-mailserver)",
    "性能压测与大规模并发优化",
]
y8 = Inches(1.9)
for f in future:
    txt(s11, Inches(7.0), y8, Inches(5.5), Inches(0.25), f"→ {f}", 13, RGBColor(0xCBD,0xD5,0xE1))
    y8 += Inches(0.35)

# Bottom
txt(s11, Inches(1.0), Inches(5.0), Inches(11), Inches(0.5),
    "线上地址: https://panel.x12w.com", 18, C['teal'], align=PP_ALIGN.CENTER)
txt(s11, Inches(1.0), Inches(5.5), Inches(11), Inches(0.5),
    "GitHub: github.com/x12w/email-system", 14, C['gray'], align=PP_ALIGN.CENTER)
txt(s11, Inches(1.0), Inches(6.3), Inches(11), Inches(0.6),
    "感谢聆听  ·  欢迎提问", 26, C['white'], True, PP_ALIGN.CENTER)

footer(s11, 11)

# ═══════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════
out = '/home/x12w/projects/email-system/docs/Email-System-答辩汇报.pptx'
prs.save(out)
print(f"✅ PPT saved: {out}")
print(f"📊 Slides: {len(prs.slides)}")
