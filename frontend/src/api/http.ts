import axios from 'axios'

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

http.interceptors.response.use((response) => {
  const body = response.data as ApiResponse<unknown>
  if (body.code !== '0') {
    return Promise.reject(new Error(body.message || 'Request failed'))
  }
  return body.data
})

export default http

