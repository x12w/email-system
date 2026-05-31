import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/auth'
import { getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string>(localStorage.getItem('accessToken') || '')
  const refreshToken = ref<string>(localStorage.getItem('refreshToken') || '')
  const user = ref<UserInfo | null>(null)

  // 从 localStorage 恢复用户信息
  const storedUser = localStorage.getItem('user')
  if (storedUser) {
    try {
      user.value = JSON.parse(storedUser)
    } catch {
      localStorage.removeItem('user')
    }
  }

  const isAuthenticated = computed(() => !!accessToken.value)

  // ---------- Token 自动刷新队列管理 ----------
  // 防止多个请求同时触发刷新，共享同一个刷新 Promise
  let refreshPromise: Promise<boolean> | null = null

  function setSession(token: string, refresh: string, userInfo: UserInfo) {
    accessToken.value = token
    refreshToken.value = refresh
    user.value = userInfo
    localStorage.setItem('accessToken', token)
    localStorage.setItem('refreshToken', refresh)
    localStorage.setItem('user', JSON.stringify(userInfo))
  }

  function clearSession() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
  }

  /**
   * 获取当前用户信息（用于页面刷新后恢复用户状态）
   */
  async function fetchCurrentUser(): Promise<UserInfo | null> {
    if (!accessToken.value) return null
    try {
      const userInfo = await getCurrentUser()
      user.value = userInfo
      localStorage.setItem('user', JSON.stringify(userInfo))
      return userInfo
    } catch {
      // Token 无效，清理状态
      clearSession()
      return null
    }
  }

  /**
   * 尝试刷新 accessToken。
   * 使用队列机制避免多个 401 请求同时刷新。
   * @returns true 表示刷新成功，false 表示刷新失败（需跳转登录）
   */
  async function tryRefreshToken(): Promise<boolean> {
    // 没有 refreshToken 则直接失败
    if (!refreshToken.value) return false

    // 如果已经在刷新中，复用同一个 Promise
    if (refreshPromise) return refreshPromise

    refreshPromise = (async () => {
      try {
        const { refreshToken: refreshFn } = await import('@/api/auth')
        const result = await refreshFn({ refreshToken: refreshToken.value })
        // 更新 token（用户信息沿用现有）
        accessToken.value = result.accessToken
        refreshToken.value = result.refreshToken
        localStorage.setItem('accessToken', result.accessToken)
        localStorage.setItem('refreshToken', result.refreshToken)
        if (result.user) {
          user.value = result.user
          localStorage.setItem('user', JSON.stringify(result.user))
        }
        return true
      } catch {
        clearSession()
        return false
      } finally {
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated,
    setSession,
    clearSession,
    fetchCurrentUser,
    tryRefreshToken,
  }
})
