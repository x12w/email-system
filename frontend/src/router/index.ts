import { createRouter, createWebHistory } from 'vue-router'

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

export default router

