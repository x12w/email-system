import http from './http'

export interface PageResult<T> {
  records: T[]
  page: number
  size: number
  total: number
}

export interface MailAccount {
  id: number
  emailAddress: string
  displayName: string
  smtpHost: string
  smtpPort: number
  smtpSsl: boolean
  imapHost: string
  imapPort: number
  imapSsl: boolean
  authUsername: string
  status: number
}

export interface Folder {
  id: number
  accountId: number
  name: string
  remoteName: string
  type: string
  unreadCount: number
  totalCount: number
}

export interface MessageSummary {
  id: number
  accountId: number
  folderId: number
  fromAddress: string
  fromName: string
  subject: string
  preview: string
  receivedAt: string
  read: boolean
  starred: boolean
  draft: boolean
  attachmentCount: number
  spamLabel: string
  priorityLabel: string
  riskLevel: string
}

export interface MessageDetail extends MessageSummary {
  to: string[]
  cc: string[]
  bcc: string[]
  contentType: string
  content: string
  sentAt: string
}

export interface SendMessageRequest {
  accountId: number
  to: string[]
  cc: string[]
  bcc: string[]
  subject: string
  contentType: string
  content: string
  attachmentIds: number[]
}

export interface IntelligenceResult {
  messageId: number
  spamLabel: string
  spamScore: number
  priorityLabel: string
  priorityScore: number
  riskLevel: string
  riskScore: number
  pluginName: string
  pluginVersion: string
  analyzedAt: string
  threats: Array<{
    type: string
    value: string
    riskLevel: string
    reason: string
  }>
}

export interface Contact {
  id: number
  name: string
  emailAddress: string
  phone: string
  remark: string
}

export interface PushEvent {
  id: number
  messageId: number
  eventType: string
  title: string
  content: string
  priority: string
  read: boolean
  pushedAt: string
}

export interface PluginStatus {
  name: string
  version: string
  runtime: string
  enabled: boolean
  timeoutMs: number
  status: string
}

export function listAccounts() {
  return http.get<unknown, MailAccount[]>('/mail-accounts')
}

export function listFolders() {
  return http.get<unknown, Folder[]>('/folders')
}

export function listMessages(params: Record<string, unknown>) {
  return http.get<unknown, PageResult<MessageSummary>>('/messages', { params })
}

export function getMessage(id: number) {
  return http.get<unknown, MessageDetail>(`/messages/${id}`)
}

export function sendMessage(data: SendMessageRequest) {
  return http.post<unknown, MessageDetail>('/messages/send', data)
}

export function saveDraft(data: SendMessageRequest) {
  return http.post<unknown, MessageDetail>('/messages/drafts', data)
}

export function markMessageRead(id: number, read: boolean) {
  return http.put<unknown, MessageDetail>(`/messages/${id}/read`, { read })
}

export function deleteMessage(id: number) {
  return http.delete<unknown, void>(`/messages/${id}`)
}

export function analyzeMessage(id: number) {
  return http.post<unknown, IntelligenceResult>(`/intelligence/messages/${id}/analyze`)
}

export function getIntelligenceResult(id: number) {
  return http.get<unknown, IntelligenceResult>(`/intelligence/messages/${id}`)
}

export function listContacts(keyword = '') {
  return http.get<unknown, Contact[]>('/contacts', { params: { keyword } })
}

export function createContact(data: Omit<Contact, 'id'>) {
  return http.post<unknown, Contact>('/contacts', data)
}

export function listPushEvents() {
  return http.get<unknown, PushEvent[]>('/intelligence/push-events')
}

export function markPushEventRead(id: number) {
  return http.put<unknown, PushEvent>(`/intelligence/push-events/${id}/read`)
}

export function listPlugins() {
  return http.get<unknown, PluginStatus[]>('/intelligence/plugins')
}
