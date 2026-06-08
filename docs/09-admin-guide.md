# 管理员使用与运维说明

本文档面向系统管理员、部署人员和二次开发人员，说明系统后台管理边界、账号权限、服务启停、配置项、数据维护、日志排查和安全要求。

## 管理范围

当前项目提供的是邮件系统 MVP 和演示级管理能力，管理功能分为三类：

| 类型 | 当前状态 | 说明 |
| --- | --- | --- |
| 业务后台接口 | 已提供基础接口 | 用户登录、邮件、联系人、附件、智能分析、插件状态 |
| 管理系统后台页面 | 待独立建设 | 可基于现有前端新增 `/admin` 路由 |
| 基础设施管理 | 通过 Docker/配置文件完成 | MySQL、Redis、MinIO、Mailpit、Nginx |

当前默认管理员：

```text
admin / password
```

生产环境必须替换默认账号、JWT 密钥、数据库密码、Redis 密码和 MinIO 密钥。

## 服务架构

| 服务 | 默认端口 | 管理职责 |
| --- | --- | --- |
| frontend | `5173` 或 Nginx `80` | 用户界面、后续可扩展管理后台 |
| backend | `8080` | REST API、认证、邮件业务、智能分析编排 |
| mysql | `3306` | 业务数据持久化 |
| redis | `6379` | 缓存、队列、token 黑名单预留 |
| minio | `9000`, `9001` | 附件对象存储 |
| mailpit | `1025`, `8025` | 本地 SMTP 测试和邮件查看 |
| nginx | `80` | 前端静态资源和 API 反向代理 |

## 启停命令

### 启动基础依赖

```bash
docker compose up -d mysql redis minio mailpit
```

### 启动完整 Docker 服务

前端构建完成后，可使用：

```bash
docker compose --profile app up -d --build
```

### 本地开发启动

后端：

```bash
cd backend
mvn spring-boot:run
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 管理后台规划

建议在前端新增 `/admin` 管理后台，使用当前鉴权体系复用 `Authorization: Bearer <accessToken>`。

推荐后台模块：

| 模块 | 管理能力 |
| --- | --- |
| 用户管理 | 用户启停、角色绑定、密码重置 |
| 邮箱账号管理 | 查看账号、禁用异常账号、测试 SMTP/IMAP |
| 邮件审计 | 搜索邮件、查看风险标签、处理误判 |
| 附件管理 | 查看附件大小、存储类型、下载审计 |
| 联系人管理 | 用户联系人查询、重复联系人清理 |
| 智能插件管理 | 插件版本、启停、超时配置、失败率 |
| 推送管理 | 未读推送、风险推送、重试状态 |
| 系统配置 | JWT、存储、邮件服务、Redis 配置检查 |
| 日志审计 | 登录审计、操作审计、异常事件 |

后端建议新增 `admin` 包：

```text
backend/src/main/java/com/example/emailsystem/admin/
  controller/
  dto/
  service/
  service/impl/
```

后台 API 建议统一使用：

```text
/api/admin/**
```

## 当前接口清单

管理员可使用现有接口完成基本检查：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/auth/login` | 登录 |
| `GET` | `/api/auth/me` | 当前用户 |
| `GET` | `/api/mail-accounts` | 邮箱账号列表 |
| `POST` | `/api/mail-accounts/{id}/test` | 测试邮箱配置 |
| `GET` | `/api/folders` | 文件夹列表 |
| `GET` | `/api/messages` | 邮件列表 |
| `GET` | `/api/intelligence/plugins` | 智能插件状态 |
| `GET` | `/api/intelligence/push-events` | 推送事件 |

示例登录：

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"password"}'
```

示例调用受保护接口：

```bash
curl http://localhost:8080/api/messages \
  -H "Authorization: Bearer <accessToken>"
```

## 配置管理

核心配置在：

```text
backend/src/main/resources/application.yml
backend/src/main/resources/application-dev.yml
```

生产环境建议使用环境变量覆盖：

| 环境变量 | 说明 |
| --- | --- |
| `JWT_SECRET` | JWT/HMAC 签名密钥，至少 32 字节 |
| `JWT_EXPIRE_SECONDS` | access token 过期时间 |
| `MYSQL_USER` | MySQL 用户 |
| `MYSQL_PASSWORD` | MySQL 密码 |
| `REDIS_PASSWORD` | Redis 密码 |
| `STORAGE_TYPE` | `local` 或 `minio` |
| `MINIO_ENDPOINT` | MinIO API 地址 |
| `MINIO_ROOT_USER` | MinIO 管理账号 |
| `MINIO_ROOT_PASSWORD` | MinIO 管理密码 |
| `MINIO_BUCKET` | 附件桶名称 |
| `INTELLIGENCE_PLUGIN_ENABLED` | 智能插件启停 |
| `INTELLIGENCE_PLUGIN_TIMEOUT_MS` | 插件调用超时时间 |

## 数据库管理

数据库结构由迁移脚本维护：

```text
backend/src/main/resources/db/migration/V1__init_schema.sql
```

表结构说明见：

```text
docs/04-database-schema.md
```

管理员需要重点关注：

| 表 | 管理重点 |
| --- | --- |
| `sys_user` | 账号状态、软删除 |
| `mail_account` | 邮箱配置、同步状态 |
| `mail_message` | 邮件数量、删除标记 |
| `mail_attachment` | 附件大小、存储路径 |
| `mail_intelligence_result` | 智能分析状态和错误 |
| `mail_threat_indicator` | 高风险命中项 |
| `mail_push_event` | 推送是否已读 |
| `login_audit` | 登录成功/失败记录 |

## 日志与排查

### 后端无法启动

检查：

1. JDK 是否为 17 或 21。
2. MySQL 是否启动。
3. Redis 密码是否匹配。
4. `server.port` 是否被占用。
5. Maven 依赖是否下载成功。

### 登录失败

检查：

1. 用户名密码是否正确。
2. `JWT_SECRET` 是否为空或过短。
3. 前端 `VITE_API_BASE_URL` 是否指向正确后端。
4. 浏览器是否存在旧 token，可清理 localStorage 后重试。

### 邮件列表为空

检查：

1. 是否选择了错误文件夹。
2. 是否启用了筛选条件。
3. 后端是否重启导致演示内存数据恢复。
4. 后续真实库模式下检查 `mail_message` 数据。

### 智能分析异常

检查：

1. `/api/intelligence/plugins` 是否返回 `ready`。
2. 插件是否启用。
3. `INTELLIGENCE_PLUGIN_TIMEOUT_MS` 是否过短。
4. Python native 插件模式下检查动态库路径和 ABI。

## 备份建议

生产环境至少备份：

| 数据 | 建议策略 |
| --- | --- |
| MySQL | 每日全量，关键系统增加 binlog 增量 |
| MinIO | 桶级备份或对象存储复制 |
| Redis | 如果保存关键队列，启用 AOF |
| 配置 | 使用密钥管理系统和配置仓库 |
| 插件产物 | 按版本归档并记录 checksum |

## 安全要求

1. 禁止生产环境使用默认密码。
2. JWT 密钥至少 32 字节，并定期轮换。
3. 管理后台必须使用 HTTPS。
4. 管理接口必须校验角色和权限。
5. 邮件附件下载必须校验归属用户。
6. 高风险邮件链接默认不应自动打开。
7. MinIO 管理控制台不应暴露到公网。
8. 登录失败和关键操作应写入审计日志。
9. 智能插件动态库应校验 checksum。
10. 生产环境禁用详细异常堆栈返回。

## 后续后台开发建议

管理后台建议按以下顺序补齐：

1. 新增角色和权限模型。
2. 新增 `/api/admin/users` 用户管理接口。
3. 新增 `/api/admin/mail-accounts` 邮箱账号管理接口。
4. 新增 `/api/admin/storage/attachments` 附件巡检接口。
5. 新增 `/api/admin/intelligence/plugins` 插件启停接口。
6. 新增 `/admin` 前端路由和管理布局。
7. 新增登录审计、操作审计和导出功能。
