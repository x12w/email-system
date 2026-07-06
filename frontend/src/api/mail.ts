import http from './http'

export interface MailAccount {
  id: number
  emailAddress: string
  displayName: string
  smtpHost: string
  smtpPort: number
  smtpSsl: number
  imapHost: string
  imapPort: number
  imapSsl: number
  authUsername: string
  status: number
  lastSyncAt: string | null
  createdAt: string
}

export interface CreateMailAccountRequest {
  emailAddress: string
  displayName?: string
  smtpHost: string
  smtpPort: number
  smtpSsl?: number
  imapHost: string
  imapPort: number
  imapSsl?: number
  authUsername: string
  authPassword: string
}

export interface UpdateMailAccountRequest {
  emailAddress: string
  displayName?: string
  smtpHost: string
  smtpPort: number
  smtpSsl?: number
  imapHost: string
  imapPort: number
  imapSsl?: number
  authUsername: string
  authPassword?: string
}

export interface SendMessageRequest {
  accountId: number
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  contentType?: string
  content?: string
  attachmentIds?: number[]
}

export interface MessageResponse {
  id: number
  accountId: number
  fromAddress: string
  fromName: string
  subject: string
  sentAt: string
  draftFlag: number
}

export interface AttachmentResponse {
  id: number
  originalName: string
  contentType: string
  sizeBytes: number
  createdAt: string
}

// Mail Accounts
export function listAccounts() {
  return http.get<unknown, MailAccount[]>('/mail-accounts')
}

export function createAccount(data: CreateMailAccountRequest) {
  return http.post<unknown, MailAccount>('/mail-accounts', data)
}

export function updateAccount(id: number, data: UpdateMailAccountRequest) {
  return http.put<unknown, MailAccount>(`/mail-accounts/${id}`, data)
}

export function deleteAccount(id: number) {
  return http.delete<unknown, void>(`/mail-accounts/${id}`)
}

export function testAccount(id: number) {
  return http.post<unknown, void>(`/mail-accounts/${id}/test`)
}

export interface FolderResponse {
  id: number
  accountId: number
  name: string
  type: string
  unreadCount: number
  totalCount: number
}

export interface PageResult<T> {
  records: T[]
  page: number
  size: number
  total: number
}

export interface MessageDetail {
  id: number
  accountId: number
  fromAddress: string
  fromName: string
  subject: string
  contentType: string
  content: string
  sentAt: string
  readFlag: number
  starFlag: number
  attachmentCount: number
}

export interface Contact {
  id: number
  name: string
  emailAddress: string
  phone: string
  remark: string
  createdAt: string
}

export interface CreateContactRequest {
  name: string
  emailAddress: string
  phone?: string
  remark?: string
}

// Folders
export function listFolders() {
  return http.get<unknown, FolderResponse[]>('/folders')
}

// Messages
export function sendMessage(data: SendMessageRequest) {
  return http.post<unknown, MessageResponse>('/messages/send', data)
}

export function listMessages(params: { folderId?: number; keyword?: string; read?: boolean; page?: number; size?: number }) {
  return http.get<unknown, PageResult<MessageDetail>>('/messages', { params })
}

export function getMessage(id: number) {
  return http.get<unknown, MessageDetail>(`/messages/${id}`)
}

export function markMessageRead(id: number, read = true) {
  return http.put<unknown, void>(`/messages/${id}/read?read=${read}`)
}

export function deleteMessage(id: number) {
  return http.delete<unknown, void>(`/messages/${id}`)
}

// Contacts
export function listContacts() {
  return http.get<unknown, Contact[]>('/contacts')
}

export function createContact(data: CreateContactRequest) {
  return http.post<unknown, Contact>('/contacts', data)
}

export function updateContact(id: number, data: CreateContactRequest) {
  return http.put<unknown, Contact>(`/contacts/${id}`, data)
}

export function deleteContact(id: number) {
  return http.delete<unknown, void>(`/contacts/${id}`)
}

// Sync
export function syncImap(accountId: number) {
  return http.post<unknown, void>(`/sync/imap/${accountId}`)
}

// Intelligence
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

export interface PushEvent {
  id: number
  messageId: number
  eventType: string
  title: string
  content: string
  priority: string
  readFlag: number
  pushedAt: string
}

export function getIntelligenceResult(messageId: number) {
  return http.get<unknown, IntelligenceResult>(`/intelligence/messages/${messageId}`)
}

export function analyzeMessage(messageId: number) {
  return http.post<unknown, IntelligenceResult>(`/intelligence/messages/${messageId}/analyze`)
}

export function listThreats(page = 1, size = 20) {
  return http.get<unknown, any[]>('/intelligence/threats', { params: { page, size } })
}

export function listPushEvents() {
  return http.get<unknown, PushEvent[]>('/intelligence/push-events')
}

export function markPushEventRead(id: number) {
  return http.put<unknown, void>(`/intelligence/push-events/${id}/read`)
}

// Attachments
export function uploadAttachment(file: File) {
  const form = new FormData()
  form.append('file', file)
  return http.post<unknown, AttachmentResponse>('/attachments', form)
}

export function downloadAttachmentUrl(id: number) {
  return `/api/attachments/${id}/download`
}
