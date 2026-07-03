import type { PaginatedData } from './api'

export interface MailRecipient {
  id?: number
  type: 'to' | 'cc' | 'bcc'
  emailAddress: string
  displayName?: string
}

export interface MailAttachment {
  id: number
  originalName: string
  contentType: string
  sizeBytes: number
}

export interface MailItem {
  id: number
  userId: number
  accountId: number
  folderId: number | null
  messageUid: string | null
  messageIdHeader: string | null
  fromAddress: string
  fromName: string | null
  subject: string | null
  contentType: string
  content: string | null
  preview: string | null
  sentAt: string | null
  receivedAt: string | null
  sizeBytes: number
  readFlag: number
  starFlag: number
  draftFlag: number
  deletedFlag: number
  attachmentCount: number
  recipients?: MailRecipient[]
  attachments?: MailAttachment[]
}

export interface SendMailRequest {
  accountId: number
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  contentType?: 'text' | 'html'
  content: string
  attachmentIds?: number[]
  /** 编辑已有草稿时传入草稿邮件 ID，后端据此执行更新而非新建 */
  draftId?: number
}

export interface MailListParams {
  accountId?: number
  folderId?: number
  keyword?: string
  read?: number
  page?: number
  size?: number
}

export type MailListResponse = PaginatedData<MailItem>

export interface MailAccount {
  id: number
  userId: number
  emailAddress: string
  displayName: string | null
  smtpHost: string
  smtpPort: number
  imapHost: string
  imapPort: number
  username: string
  sslEnabled: number
  activeFlag: number
  lastSyncAt: string | null
}

export interface MailAccountRequest {
  emailAddress: string
  displayName?: string
  smtpHost: string
  smtpPort: number
  imapHost: string
  imapPort: number
  username: string
  password: string
  sslEnabled?: number
}

// ---------- intelligence ----------

export interface ThreatIndicator {
  type: string
  value: string
  riskLevel: string
  reason: string
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
  threats: ThreatIndicator[]
}

export interface PluginStatus {
  name: string
  version: string
  runtime: string
  enabled: boolean
  timeoutMs: number
  status: string
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
