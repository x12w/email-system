import { defineStore } from 'pinia'

interface CurrentUser {
  id: number
  username: string
  displayName: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('accessToken') || '',
    user: null as CurrentUser | null
  }),
  actions: {
    setSession(token: string, user: CurrentUser) {
      this.accessToken = token
      this.user = user
      localStorage.setItem('accessToken', token)
    },
    clearSession() {
      this.accessToken = ''
      this.user = null
      localStorage.removeItem('accessToken')
    }
  }
})

