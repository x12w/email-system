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
      component: () => import('@/views/mail/MailHomeView.vue'),
      children: [
        {
          path: 'compose',
          name: 'compose',
          component: () => import('@/views/mail/MailComposeView.vue')
        },
        {
          path: 'contacts',
          name: 'contacts',
          component: () => import('@/views/mail/MailContactsView.vue')
        }
      ]
    }
  ]
})

router.beforeEach((to, _from) => {
  const token = localStorage.getItem('accessToken')
  if (to.name !== 'login' && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { name: 'mail' }
  }
})

export default router
