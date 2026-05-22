import request from '@/utils/request'
import type {
  MailItem,
  MailListParams,
  MailListResponse,
  SendMailRequest,
  MailAttachment,
} from '@/types/mail'

export function getMailList(params: MailListParams): Promise<MailListResponse> {
  return request.get('/messages', { params })
}

export function getMailDetail(id: number): Promise<MailItem> {
  return request.get(`/messages/${id}`)
}

export function sendMail(data: SendMailRequest): Promise<void> {
  return request.post('/messages/send', data)
}

export function saveDraft(data: SendMailRequest): Promise<void> {
  return request.post('/messages/drafts', data)
}

export function markAsRead(id: number): Promise<void> {
  return request.put(`/messages/${id}/read`)
}

export function markAsUnread(id: number): Promise<void> {
  return request.put(`/messages/${id}/read`, { read: false })
}

export function deleteMail(id: number): Promise<void> {
  return request.delete(`/messages/${id}`)
}

export function uploadAttachment(file: File): Promise<MailAttachment> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/attachments', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
