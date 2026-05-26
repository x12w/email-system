# Email System

基于 Vue 3 和 Spring Boot 的电子邮件系统项目。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Vue Router、Element Plus、Axios
- 后端：Spring Boot、Spring Security、JWT、MyBatis-Plus、Jakarta Mail
- 数据库：MySQL
- 缓存：Redis
- 文件存储：本地文件系统或 MinIO
- 邮件测试：Mailpit
- 部署：Docker、Docker Compose、Nginx

## 仓库结构

```text
email-system/
  frontend/        前端应用
  backend/         后端服务
  docs/            项目文档、接口约定、数据库设计、开发规范
  deploy/          Nginx、MinIO 等部署配置
  scripts/         辅助脚本
  data/            本地开发数据目录，不提交业务数据
```

## 快速阅读

- [项目结构与分支规范](docs/01-project-structure.md)
- [开发环境与启动说明](docs/02-development-guide.md)
- [前后端对接规范](docs/03-frontend-backend-contract.md)
- [数据库设计草案](docs/04-database-schema.md)
- [部署与 Docker 说明](docs/05-deployment.md)
- [开发任务拆分建议](docs/06-roadmap.md)
- [智能邮件管理模块设计](docs/07-intelligent-mail-management.md)
- [Redis 缓存设计](docs/08-redis-cache-design.md)
- [数据库前后端协同对齐接口文档](docs/09-database-api-alignment.md)

## 开发约定

1. 主分支保留稳定代码：`main`
2. 集成分支用于联调：`develop`
3. 功能分支从 `develop` 切出：`feature/<module>-<description>`
4. 修复分支从 `develop` 或 `main` 切出：`fix/<issue>-<description>`
5. 提交前至少完成本地构建、静态检查和相关接口自测。
