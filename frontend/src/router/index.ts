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

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('accessToken')
  if (to.meta.requiresAuth !== false && !token) {
    next({ name: 'login' })
  } else if (to.name === 'login' && token) {
    next({ name: 'mail' })
  } else {
    next()
  }
})

export default router
