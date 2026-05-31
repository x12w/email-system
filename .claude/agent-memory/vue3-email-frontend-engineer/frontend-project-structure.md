---
name: frontend-project-structure
description: 前端项目目录结构、分支规范、提交规范、合并要求
metadata:
  type: reference
---

## 前端目录结构

```
frontend/
  src/
    api/            Axios 实例、接口请求函数、按模块拆分
      auth.ts       登录、刷新token、退出、当前用户
      mail.ts       邮件列表、详情、发送、草稿、附件、邮箱账号
      folder.ts     文件夹列表、同步
      contact.ts    联系人CRUD
      intelligence.ts  AI智能分析（待实现）
    assets/         图片、字体等静态资源
    components/     可复用 UI 组件
    layouts/        布局组件
      MainLayout.vue  主应用布局（侧边栏+顶栏+内容区）
    router/         Vue Router 路由表、路由守卫
      index.ts      路由定义 + beforeEach 守卫
    stores/         Pinia 状态管理
      auth.ts       当前用户、token、权限
      mail.ts       邮件列表状态、筛选条件
    styles/         全局样式、Element Plus 主题变量
      main.css      全局样式入口
    types/          TypeScript 类型定义
      api.d.ts      通用响应、分页类型
      auth.d.ts     认证相关类型
      mail.d.ts     邮件相关类型
      folder.d.ts   文件夹相关类型
      contact.d.ts  联系人相关类型
    utils/          通用工具函数
      request.ts    Axios 实例、拦截器
    views/          页面级组件（按模块分子目录）
      auth/         登录页等
      mail/         邮件首页、详情、撰写
      contacts/     联系人列表
      settings/     设置页
    App.vue         根组件（<router-view />）
    main.ts         应用入口（挂载 Pinia、Router、Element Plus）
```

## 分支规范

| 分支 | 用途 |
| --- | --- |
| `main` | 生产或稳定版本，只接收已验证的合并 |
| `develop` | 日常集成和联调分支 |
| `feature/<module>-<desc>` | 功能开发，例如 `feature/mail-compose` |
| `fix/<issue>-<desc>` | 缺陷修复，例如 `fix/login-token-expire` |
| `release/<version>` | 发布准备，例如 `release/1.0.0` |
| `hotfix/<version-or-issue>` | 生产紧急修复 |

**当前工作分支**：`feat/fronted_design`

## 提交规范

使用 Conventional Commits 风格：

```text
feat(auth): add jwt login api
fix(mail): handle attachment filename decode
docs(db): add initial schema
chore(docker): add compose services
```

## 合并要求

1. 功能分支只合并到 `develop`
2. `develop` 验证通过后再合并到 `main`
3. PR 描述需要包含变更范围、测试方式、数据库变更、配置变更
4. 涉及接口变更时，同步更新 `docs/03-frontend-backend-contract.md`
5. 涉及表结构变更时，同步更新 `docs/04-database-schema.md` 和迁移脚本
