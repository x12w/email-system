import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

export interface ApiResponse<T> {
  code: string
  message: string
  data: T
}

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response): any => {
    const body = response.data as ApiResponse<unknown>
    if (body.code !== '0') {
      return Promise.reject(new Error(body.message || 'Request failed'))
    }
    return body.data
  },
  async (error) => {
    if (error.response?.status === 401 || error.response?.data?.code === 'AUTH_401') {
      useAuthStore().clearSession()
      if (router.currentRoute.value.path !== '/login') {
        await router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

export default http
