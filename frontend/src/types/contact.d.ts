import type { PaginatedData } from './api'

export interface ContactItem {
  id: number
  userId: number
  name: string
  emailAddress: string
  phone: string | null
  company: string | null
  department: string | null
  remark: string | null
}

export interface ContactRequest {
  name: string
  emailAddress: string
  phone?: string
  company?: string
  department?: string
  remark?: string
}

export interface ContactListParams {
  keyword?: string
  page?: number
  size?: number
}

export type ContactListResponse = PaginatedData<ContactItem>
