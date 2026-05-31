import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types/api'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

// 标记是否正在刷新 token（跨请求共享）
let isRefreshing = false
// 刷新期间挂起的请求队列
let pendingQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

/**
 * 处理 Token 过期：尝试刷新，成功则用新 token 重试队列中的请求
 */
async function handleTokenExpired(): Promise<string> {
  // 动态导入避免循环依赖
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  const success = await authStore.tryRefreshToken()
  if (!success) {
    pendingQueue.forEach((p) => p.reject(new Error('Token 刷新失败，请重新登录')))
    pendingQueue = []
    throw new Error('Token 刷新失败')
  }

  const newToken = authStore.accessToken
  pendingQueue.forEach((p) => p.resolve(newToken))
  pendingQueue = []
  return newToken
}

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse<unknown>
    if (body.code !== '0') {
      if (body.code === 'AUTH_401') {
        return handleTokenExpired().then((newToken) => {
          // 用新 token 重试原请求
          if (response.config) {
            response.config.headers.Authorization = `Bearer ${newToken}`
            return http.request(response.config)
          }
          return Promise.reject(new Error(body.message || 'Request failed'))
        }).catch(() => {
          window.location.href = '/login'
          return Promise.reject(new Error(body.message || 'Request failed'))
        })
      }
      return Promise.reject(new Error(body.message || 'Request failed'))
    }
    return body.data as any
  },
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // HTTP 401 且未重试过 → 尝试刷新 token 并重试
    if (error.response?.status === 401 && !config?._retry) {
      config._retry = true
      try {
        const newToken = await handleTokenExpired()
        config.headers.Authorization = `Bearer ${newToken}`
        return http.request(config)
      } catch {
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    // 已经重试过还是 401 → 直接跳转登录
    if (error.response?.status === 401 && config?._retry) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  },
)

const request = http as unknown as {
  get<T = unknown>(url: string, config?: Record<string, unknown>): Promise<T>
  post<T = unknown>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T>
  put<T = unknown>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T>
  delete<T = unknown>(url: string, config?: Record<string, unknown>): Promise<T>
}

export default request
