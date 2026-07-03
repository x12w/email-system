import request from '@/utils/request'
import type {
  IntelligenceResult,
  MailItem,
  MailListParams,
  MailListResponse,
  PluginStatus,
  PushEvent,
  SendMailRequest,
  MailAttachment,
  MailAccount,
  MailAccountRequest,
  ThreatIndicator,
} from '@/types/mail'

// ---------- messages ----------

export function getMailList(params: MailListParams): Promise<MailListResponse> {
  return request.get('/messages', { params })
}

export function getMailDetail(id: number): Promise<MailItem> {
  return request.get(`/messages/${id}`)
}

export function sendMail(data: SendMailRequest): Promise<void> {
  return request.post('/messages/send', data)
}

/**
 * 保存草稿（新建草稿，后端只提供 POST /api/messages/drafts）。
 */
export function saveDraft(data: SendMailRequest): Promise<{ id: number }> {
  return request.post('/messages/drafts', data)
}

export function markAsRead(id: number): Promise<void> {
  return request.put(`/messages/${id}/read`, { read: true })
}

export function markAsUnread(id: number): Promise<void> {
  return request.put(`/messages/${id}/read`, { read: false })
}

export function deleteMail(id: number): Promise<void> {
  return request.delete(`/messages/${id}`)
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

export function createMailAccount(data: MailAccountRequest): Promise<void> {
  return request.post('/mail-accounts', data)
}

export function updateMailAccount(id: number, data: Partial<MailAccountRequest>): Promise<void> {
  return request.put(`/mail-accounts/${id}`, data)
}

export function deleteMailAccount(id: number): Promise<void> {
  return request.delete(`/mail-accounts/${id}`)
}

export function testMailAccount(id: number): Promise<void> {
  return request.post(`/mail-accounts/${id}/test`)
}

// ---------- intelligence ----------

export function analyzeMessage(id: number): Promise<IntelligenceResult> {
  return request.post(`/intelligence/messages/${id}/analyze`)
}

export function getIntelligenceResult(id: number): Promise<IntelligenceResult> {
  return request.get(`/intelligence/messages/${id}`)
}

export function listPlugins(): Promise<PluginStatus[]> {
  return request.get('/intelligence/plugins')
}

export function listPushEvents(): Promise<PushEvent[]> {
  return request.get('/intelligence/push-events')
}

export function markPushEventRead(id: number): Promise<PushEvent> {
  return request.put(`/intelligence/push-events/${id}/read`)
}

export function getThreats(): Promise<ThreatIndicator[]> {
  return request.get('/intelligence/threats')
}
