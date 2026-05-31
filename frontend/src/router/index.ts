import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'mail',
          component: () => import('@/views/mail/MailHomeView.vue'),
        },
        {
          path: 'mail/:id',
          name: 'mail-detail',
          component: () => import('@/views/mail/MailDetailView.vue'),
        },
        {
          path: 'compose',
          name: 'mail-compose',
          component: () => import('@/views/mail/MailComposeView.vue'),
        },
        {
          path: 'contacts',
          name: 'contacts',
          component: () => import('@/views/contacts/ContactListView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/settings/SettingsView.vue'),
        },
      ],
    },
  ],
})

// 标记是否已完成首次用户信息加载
let userFetched = false

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('accessToken')

  // 未登录 → 需要认证的页面 → 重定向登录
  if (to.meta.requiresAuth !== false && !token) {
    next({ name: 'login' })
    return
  }

  // 已登录 → 访问登录页 → 重定向到首页
  if (to.name === 'login' && token) {
    next({ name: 'mail' })
    return
  }

  // 已登录 + 未加载用户信息 → 先获取用户信息再放行
  if (token && !userFetched) {
    userFetched = true
    try {
      const { useAuthStore } = await import('@/stores/auth')
      const authStore = useAuthStore()
      await authStore.fetchCurrentUser()
    } catch {
      // 获取失败不阻塞路由（拦截器会处理 401）
    }
  }

  next()
})

export default router
