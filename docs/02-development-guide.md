# 开发环境与启动说明

## 本地依赖

- JDK 17 或 21
- Maven 3.9+
- Node.js 20+
- pnpm 9+ 或 npm
- Docker 与 Docker Compose
- MySQL 8.0
- Redis 7

## 环境变量

复制环境模板：

```bash
cp .env.example .env
```

本地开发建议不要提交 `.env`。生产环境必须替换 JWT、数据库、MinIO 密码。

## 前端初始化建议

在 `frontend/` 下使用 Vite 初始化 Vue 3 + TypeScript 项目：

```bash
cd frontend
pnpm create vite . --template vue-ts
pnpm add pinia vue-router element-plus axios
pnpm add -D unplugin-auto-import unplugin-vue-components
pnpm dev
```

推荐前端模块拆分：

| 模块 | 说明 |
| --- | --- |
| `api/auth.ts` | 登录、刷新 token、退出 |
| `api/mail.ts` | 邮件列表、详情、发送、草稿 |
| `api/folder.ts` | 文件夹列表、未读数 |
| `api/contact.ts` | 联系人 CRUD |
| `stores/auth.ts` | 当前用户、token、权限 |
| `stores/mail.ts` | 邮件列表状态、筛选条件 |

## 后端初始化建议

在 `backend/` 下创建 Spring Boot 项目，建议依赖：

- Spring Web
- Spring Security
- Validation
- MyBatis-Plus
- MySQL Driver
- Spring Data Redis
- Jakarta Mail
- Lombok
- MinIO Java SDK
- Flyway 或 Liquibase
- JNA 或 JNI 封装，用于加载智能分析动态库插件

建议包名：`com.example.emailsystem`。

## 后端配置建议

`application.yml` 分环境：

```text
application.yml
application-dev.yml
application-prod.yml
```

核心配置项：

| 配置 | 说明 |
| --- | --- |
| `spring.datasource.*` | MySQL 连接 |
| `spring.data.redis.*` | Redis 连接 |
| `security.jwt.secret` | JWT 签名密钥 |
| `mail.default-provider` | 默认邮件服务配置 |
| `storage.type` | `local` 或 `minio` |
| `storage.local.root-path` | 本地附件存储目录 |
| `storage.minio.*` | MinIO 连接和桶 |
| `intelligence.plugin.*` | 智能邮件分析插件配置 |

## Python 智能插件开发建议

智能邮件管理的 Python 代码放在 `plugins/intelligence/python/`。开发阶段先保证 `analyze_email_json(request_json)` 的 JSON 输入输出稳定，再考虑打包为 `.dll`、`.so` 或 `.dylib`。

本地调试建议：

```bash
cd plugins/intelligence/python
python -m pytest
```

打包产物统一放到 `plugins/intelligence/native/`，由后端配置项 `intelligence.plugin.artifact-path` 指向具体文件。插件不可用时，后端应将分析状态记录为 `failed` 或 `timeout`，不能阻断邮件入库。

## 联调顺序

1. 启动 MySQL、Redis、Mailpit、MinIO。
2. 后端运行数据库迁移脚本。
3. 后端启动并暴露 `http://localhost:8080/api`。
4. 前端配置 `VITE_API_BASE_URL=http://localhost:8080/api`。
5. 使用 Mailpit Web UI 验证发信：`http://localhost:8025`。

## 质量检查

前端建议：

```bash
pnpm type-check
pnpm lint
pnpm build
```

后端建议：

```bash
mvn test
mvn package
```
