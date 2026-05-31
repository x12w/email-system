# 项目结构与分支规范

## 目录职责

```text
frontend/
  src/api/          Axios 实例、接口请求函数、接口模块拆分
  src/assets/       图片、字体等静态资源
  src/components/   可复用 UI 组件
  src/layouts/      登录布局、主应用布局
  src/router/       Vue Router 路由表、路由守卫
  src/stores/       Pinia 状态管理
  src/styles/       全局样式、Element Plus 主题变量
  src/types/        TypeScript 类型定义
  src/utils/        通用工具函数
  src/views/        页面级组件

backend/
  src/main/java/com/example/emailsystem/
    common/         统一响应、异常、分页、常量
    config/         Spring、Security、MyBatis、Redis、存储配置
    controller/     REST API 控制器
    dto/            请求 DTO、响应 VO、转换对象
    entity/         MyBatis-Plus 实体
    mapper/         Mapper 接口
    security/       JWT、认证过滤器、用户上下文
    service/        业务接口
    service/impl/   业务实现
    mail/           收信、发信、解析、同步相关逻辑
    intelligence/   智能邮件管理：分类、风险检测、插件编排、推送触发
    storage/        本地文件系统和 MinIO 适配
    job/            定时任务，例如邮件同步、清理任务
  src/main/resources/
    mapper/         MyBatis XML
    db/migration/   数据库迁移脚本（历史参考，生产以 deploy/mysql/init.sql 为准）

deploy/
  nginx/            前端静态资源代理和后端 API 反向代理配置
  redis/            Redis 生产配置与 Dockerfile
  minio/            MinIO 初始化脚本与桶策略配置
  mysql/            数据库初始化脚本

plugins/
  intelligence/
    python/         Python 智能分析插件源码、模型、测试
    native/         Python 打包后的 dll/so/dylib 插件产物

docs/               开发文档、接口约定、数据库设计
scripts/            本地开发、部署辅助脚本
data/               Docker Compose 本地数据挂载目录
```

## 智能邮件管理模块职责

后端 Java 模块 `backend/src/main/java/com/example/emailsystem/intelligence/` 只负责业务编排，不直接写模型逻辑：

| 子目录 | 职责 |
| --- | --- |
| `dto/` | 邮件分析请求、分析结果、风险项、推送事件 DTO |
| `plugin/` | dll/so 插件加载、版本校验、超时控制、熔断降级 |
| `service/` | 分析任务编排、结果入库、标签更新、推送触发 |

Python 插件模块 `plugins/intelligence/python/` 负责真正的智能判断：

| 子目录 | 职责 |
| --- | --- |
| `src/` | 垃圾邮件识别、高优先级识别、恶意链接检测、特征提取 |
| `models/` | 本地模型、规则词典、域名信誉库等资源 |
| `tests/` | 插件单元测试、样本回归测试 |

`plugins/intelligence/native/` 只放打包产物，例如 Windows 的 `.dll`、Linux 的 `.so`、macOS 的 `.dylib`。源码和产物分离，避免 Java 后端直接依赖 Python 工程内部路径。

## 分支规范

| 分支 | 用途 |
| --- | --- |
| `main` | 生产或稳定版本，只接收已验证的合并 |
| `develop` | 日常集成和联调分支 |
| `feature/<module>-<desc>` | 功能开发，例如 `feature/mail-compose` |
| `fix/<issue>-<desc>` | 缺陷修复，例如 `fix/login-token-expire` |
| `release/<version>` | 发布准备，例如 `release/1.0.0` |
| `hotfix/<version-or-issue>` | 生产紧急修复 |

## 建议创建分支流程

```bash
git checkout main
git pull
git checkout -b develop
git push -u origin develop

git checkout develop
git checkout -b feature/auth-login
```

## 提交信息建议

使用简洁的 Conventional Commits 风格：

```text
feat(auth): add jwt login api
fix(mail): handle attachment filename decode
feat(intelligence): add spam and threat analysis plugin
docs(db): add initial schema
chore(docker): add compose services
```

## 合并要求

1. 功能分支只合并到 `develop`。
2. `develop` 验证通过后再合并到 `main`。
3. PR 描述需要包含变更范围、测试方式、数据库变更、配置变更。
4. 涉及接口变更时，同步更新 `docs/03-frontend-backend-contract.md`。
5. 涉及表结构变更时，同步更新 `docs/04-database-schema.md` 和迁移脚本。
6. 涉及智能插件 ABI 变更时，同步更新 `docs/07-intelligent-mail-management.md`，并保留兼容版本。
