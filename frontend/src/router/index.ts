import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue')
    },
    {
      path: '/',
      name: 'mail',
      component: () => import('@/views/mail/MailHomeView.vue')
    }
  ]
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.path !== '/login' && !authStore.accessToken) {
    return '/login'
  }
  if (to.path === '/login' && authStore.accessToken) {
    return '/'
  }
  return true
})

export default router
