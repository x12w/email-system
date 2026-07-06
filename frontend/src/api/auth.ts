import http from './http'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  expiresIn: number
  user: {
    id: number
    username: string
    displayName: string
  }
}

export function login(data: LoginRequest) {
  return http.post<unknown, LoginResponse>('/auth/login', data)
}

export function getCurrentUser() {
  return http.get<unknown, LoginResponse['user']>('/auth/me')
}

