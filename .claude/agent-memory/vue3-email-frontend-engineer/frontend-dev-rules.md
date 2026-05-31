---
name: frontend-dev-rules
description: 前端开发规范：核心依赖、模块拆分、Axios 约定、代码风格、质量检查标准
metadata:
  type: reference
---

## 核心依赖

- Vue 3 + TypeScript（`<script setup lang="ts">`）
- Pinia（Composition API 风格，`defineStore` + `ref`/`computed`）
- Vue Router 4（`createWebHistory`，路由守卫 `beforeEach`）
- Element Plus（自动导入：`unplugin-auto-import` + `unplugin-vue-components`）
- Axios（统一实例 `@/utils/request.ts`）

## 模块拆分规范

### API 模块拆分

所有 API 函数放在 `frontend/src/api/` 下，按业务模块拆分：

| 文件 | 职责 | 状态 |
|------|------|------|
| `api/auth.ts` | 登录、刷新 token、退出、当前用户信息 | ✅ 已实现 |
| `api/mail.ts` | 邮件列表、详情、发送、草稿、标记已读、删除、附件上传/下载、邮箱账号管理 | ✅ 已实现 |
| `api/folder.ts` | 文件夹列表、同步远程文件夹 | ✅ 已实现 |
| `api/contact.ts` | 联系人 CRUD | ✅ 已实现 |
| `api/intelligence.ts` | AI 智能分析结果查询 | ❌ 待实现 |

每个 API 模块的编码规范：

```typescript
import request from '@/utils/request'
import type { XxxRequest, XxxResponse, XxxListParams } from '@/types/xxx'

// GET 请求：参数通过 { params } 传递
export function getXxxList(params: XxxListParams): Promise<XxxResponse> {
  return request.get('/xxx', { params })
}

// POST 请求：请求体作为第二个参数
export function createXxx(data: XxxRequest): Promise<void> {
  return request.post('/xxx', data)
}

// PUT 请求：路径参数 + 请求体
export function updateXxx(id: number, data: XxxRequest): Promise<void> {
  return request.put(`/xxx/${id}`, data)
}

// DELETE 请求：路径参数
export function deleteXxx(id: number): Promise<void> {
  return request.delete(`/xxx/${id}`)
}
```

### Store 模块拆分

| 文件 | 职责 | 关键状态 |
|------|------|----------|
| `stores/auth.ts` | 当前用户、token、认证状态 | `accessToken`, `refreshToken`, `user`, `isAuthenticated`, `setSession()`, `clearSession()` |
| `stores/mail.ts` | 邮件列表状态、筛选条件 | `mailList`, `currentMail`, `total`, `loading`, `filters`, `hasMore`, `setFilters()`, `resetMailList()` |

Store 编码规范（Composition API 风格）：

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useXxxStore = defineStore('xxx', () => {
  const data = ref<XxxType[]>([])
  const loading = ref(false)

  const hasData = computed(() => data.value.length > 0)

  function reset() {
    data.value = []
    loading.value = false
  }

  return { data, loading, hasData, reset }
})
```

### TypeScript 类型模块拆分

| 文件 | 职责 |
|------|------|
| `types/api.d.ts` | 通用类型：`ApiResponse<T>`, `PaginatedData<T>` |
| `types/auth.d.ts` | 认证相关：`LoginRequest`, `LoginResponse`, `RefreshRequest`, `UserInfo` |
| `types/mail.d.ts` | 邮件相关：`MailItem`, `SendMailRequest`, `MailListParams`, `MailListResponse`, `MailAccount`, `MailAccountRequest`, `MailRecipient`, `MailAttachment` |
| `types/folder.d.ts` | 文件夹相关：`FolderItem`, `SyncFolderRequest` |
| `types/contact.d.ts` | 联系人相关：`ContactItem`, `ContactRequest`, `ContactListParams`, `ContactListResponse` |

类型定义规范：
- 请求体接口：`XxxRequest`
- 响应数据类型：`XxxResponse`（或直接使用 `XxxItem` / `PaginatedData<XxxItem>`）
- 实体接口：`XxxItem`
- 列表参数：`XxxListParams`
- 所有字段必须有明确的类型，禁止 `any`

## Axios 约定

`@/utils/request.ts` 的约定：

1. **baseURL**：`import.meta.env.VITE_API_BASE_URL || '/api'`
2. **timeout**：15000ms
3. **请求拦截器**：从 `localStorage.getItem('accessToken')` 读取 token，统一注入 `Authorization: Bearer <token>`
4. **响应拦截器（成功）**：
   - 检查 `body.code !== '0'` → 非成功码统一 reject
   - `body.code === 'AUTH_401'` → 清理 localStorage + 跳转 `/login`
   - 成功时返回 `body.data`（即 API 函数拿到的已经是解包后的业务数据）
5. **响应拦截器（错误）**：HTTP 401 → 清理状态 + 跳转 `/login`
6. **文件上传**：使用 `multipart/form-data`，字段名 `file`

## 路由约定

当前路由结构（`router/index.ts`）：

```
/login          → LoginView（公开，requiresAuth: false）
/               → MainLayout（需认证，requiresAuth: true）
  /             → MailHomeView（邮件首页）
  /mail/:id     → MailDetailView（邮件详情）
  /compose      → MailComposeView（撰写邮件）
  /contacts     → ContactListView（联系人列表）
  /settings     → SettingsView（设置页）
```

路由守卫逻辑：
1. 目标路由需要认证 + 无 token → 重定向到 `/login`
2. 已在 `/login` + 已有 token → 重定向到 `/`（邮件首页）
3. Token 来源：`localStorage.getItem('accessToken')`

## 视图开发规范

- 使用 `<script setup lang="ts">` 语法
- 页面级组件放在 `views/` 对应子目录下
- 必须处理三种状态：**加载中**（`v-loading`）、**空数据**（`el-empty`）、**错误**（`el-alert` 或 `ElMessage.error`）
- 使用 Element Plus 组件时无需手动导入（自动导入已配置）
- 组件命名：PascalCase（如 `MailComposeView.vue`）

## 布局组件规范

- **MainLayout.vue**：主应用布局，包含可折叠侧边栏（`el-menu` + router 链接）、顶栏（用户信息 + 退出登录）、内容区（`<router-view />`）
- 后续如需新增 AuthLayout，放在 `layouts/` 下

## 代码风格

1. 缩进：2 空格
2. 字符串：单引号
3. 分号：不强制（TypeScript 自动处理）
4. import 顺序：Vue 核心 → 第三方库 → 内部模块（`@/`）→ 样式
5. 变量/函数：camelCase
6. 组件文件：PascalCase
7. 类型/接口：PascalCase

## 质量检查

开发完成必须保证：

```bash
pnpm type-check   # 无类型错误
pnpm lint         # 无代码风格错误
pnpm build        # 能正常构建
```

如果有任何检查失败，必须在提交前修复。
