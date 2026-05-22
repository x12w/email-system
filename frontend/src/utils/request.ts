import axios from 'axios'
import type { ApiResponse } from '@/types/api'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

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
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(body.message || 'Request failed'))
    }
    return body.data as any
  },
  (error) => {
    if (error.response?.status === 401) {
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
