import request from '@/utils/request'
import type {
  MailItem,
  MailListParams,
  MailListResponse,
  ProcessMailRequest,
  ProcessMailResponse,
  SendMailRequest,
  MailAttachment,
  MailAccount,
  MailAccountRequest,
} from '@/types/mail'

// ---------- messages ----------

export function getMailList(params: MailListParams): Promise<MailListResponse> {
  return request.get('/messages', { params })
}

export function getMailDetail(id: number): Promise<MailItem> {
  return request.get(`/messages/${id}`)
}

export function sendMail(data: SendMailRequest): Promise<MailItem> {
  return request.post('/messages/send', data)
}

/**
 * 保存草稿（新建草稿）。
 */
export function saveDraft(data: SendMailRequest): Promise<MailItem> {
  return request.post('/messages/drafts', data)
}

export function markAsRead(id: number): Promise<MailItem> {
  return request.put(`/messages/${id}/read`, { read: true })
}

export function markAsUnread(id: number): Promise<MailItem> {
  return request.put(`/messages/${id}/read`, { read: false })
}

export function deleteMail(id: number): Promise<void> {
  return request.delete(`/messages/${id}`)
}

/**
 * 接收并处理新邮件（触发 AI 拦截分析）。
 * 对应 POST /api/messages/process
 */
export function processMail(data: ProcessMailRequest): Promise<ProcessMailResponse> {
  return request.post('/messages/process', data)
}

// ---------- attachments ----------

export function uploadAttachment(file: File): Promise<MailAttachment> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/attachments', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function downloadAttachment(id: number): Promise<Blob> {
  return request.get(`/attachments/${id}/download`, { responseType: 'blob' })
}

export function deleteAttachment(id: number): Promise<void> {
  return request.delete(`/attachments/${id}`)
}

// ---------- mail accounts ----------

export function getMailAccounts(): Promise<MailAccount[]> {
  return request.get('/mail-accounts')
}

export function createMailAccount(data: MailAccountRequest): Promise<MailAccount> {
  return request.post('/mail-accounts', data)
}

export function updateMailAccount(id: number, data: MailAccountRequest): Promise<MailAccount> {
  return request.put(`/mail-accounts/${id}`, data)
}

export function deleteMailAccount(id: number): Promise<void> {
  return request.delete(`/mail-accounts/${id}`)
}

export function testMailAccount(id: number): Promise<{ status: string; message: string }> {
  return request.post(`/mail-accounts/${id}/test`)
}
