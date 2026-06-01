import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/auth'
import { getCurrentUser } from '@/api/auth'

/**
 * 开发模式开关。
 * 读取 .env 中的 VITE_DEV_BYPASS_AUTH，为 'true' 时跳过登录流程。
 * 设为 'false' 或移除该变量即可恢复正常的登录认证。
 */
const DEV_BYPASS = import.meta.env.VITE_DEV_BYPASS_AUTH === 'true'

/**
 * 开发模式使用的模拟用户数据。
 * 仅在 DEV_BYPASS 为 true 且 localStorage 中没有用户数据时生效。
 */
const MOCK_USER: UserInfo = {
  id: 1,
  username: 'dev',
  displayName: '开发者',
  avatarUrl: '',
}

/**
 * 开发模式：模块加载时自动注入模拟登录数据到 localStorage。
 * 仅在 token 不存在时写入，避免覆盖已有的真实登录态。
 * 如果已有 token，说明用户可能之前真实登录过，保留现有数据。
 */
if (DEV_BYPASS && !localStorage.getItem('accessToken')) {
  localStorage.setItem('accessToken', 'dev-bypass-token')
  localStorage.setItem('refreshToken', 'dev-bypass-refresh')
  localStorage.setItem('user', JSON.stringify(MOCK_USER))
}

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

    /**
     * 开发模式：跳过 API 调用，直接从 localStorage 读取模拟用户数据。
     * 避免后端未就绪时 fetchCurrentUser 报错导致页面白屏。
     * 将 VITE_DEV_BYPASS_AUTH 设为 false 即可恢复真实 API 调用。
     */
    if (DEV_BYPASS) {
      const stored = localStorage.getItem('user')
      if (stored) {
        try {
          user.value = JSON.parse(stored)
          return user.value
        } catch {
          localStorage.removeItem('user')
        }
      }
      return null
    }

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
