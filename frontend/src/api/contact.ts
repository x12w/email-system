import request from '@/utils/request'
import type { ContactItem, ContactRequest, ContactListParams, ContactListResponse } from '@/types/contact'

export function getContactList(params: ContactListParams): Promise<ContactListResponse> {
  return request.get('/contacts', { params })
}

export function getContactDetail(id: number): Promise<ContactItem> {
  return request.get(`/contacts/${id}`)
}

export function createContact(data: ContactRequest): Promise<void> {
  return request.post('/contacts', data)
}

export function updateContact(id: number, data: ContactRequest): Promise<void> {
  return request.put(`/contacts/${id}`, data)
}

export function deleteContact(id: number): Promise<void> {
  return request.delete(`/contacts/${id}`)
}
