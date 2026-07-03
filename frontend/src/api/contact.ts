import request from '@/utils/request'
import type { ContactItem, ContactRequest } from '@/types/contact'

/**
 * 获取联系人列表（后端返回 List，无分页）。
 */
export function getContactList(keyword?: string): Promise<ContactItem[]> {
  return request.get('/contacts', { params: keyword ? { keyword } : {} })
}

export function createContact(data: ContactRequest): Promise<ContactItem> {
  return request.post('/contacts', data)
}

export function updateContact(id: number, data: ContactRequest): Promise<ContactItem> {
  return request.put(`/contacts/${id}`, data)
}

export function deleteContact(id: number): Promise<void> {
  return request.delete(`/contacts/${id}`)
}
