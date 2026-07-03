import type { PaginatedData } from './api'

// ---------- 邮件列表项（对应后端 MessageSummary） ----------

export interface MailSummary {
  id: number
  accountId: number
  folderId: number
  fromAddress: string
  fromName: string | null
  subject: string | null
  preview: string | null
  receivedAt: string | null
  read: boolean
  starred: boolean
  draft: boolean
  attachmentCount: number
  spamLabel: string
  priorityLabel: string
  riskLevel: string
}

// ---------- 邮件详情（对应后端 MessageDetail） ----------

export interface MailItem {
  id: number
  accountId: number
  folderId: number
  fromAddress: string
  fromName: string | null
  to: string[]
  cc: string[]
  bcc: string[]
  subject: string | null
  contentType: string
  content: string | null
  preview: string | null
  sentAt: string | null
  receivedAt: string | null
  read: boolean
  starred: boolean
  draft: boolean
  attachmentCount: number
  spamLabel: string
  priorityLabel: string
  riskLevel: string
  /** 附件列表（前端扩展字段，用于详情展示） */
  attachments?: MailAttachment[]
}

// ---------- 邮件附件 ----------

export interface MailAttachment {
  id: number
  originalName: string
  contentType: string
  sizeBytes: number
  /** 后端返回的下载 URL 或存储标识 */
  storageType?: string
  downloadUrl?: string
}

// ---------- 发送/保存草稿请求（对应后端 SendMessageRequest） ----------

export interface SendMailRequest {
  accountId: number
  to: string[]
  cc?: string[]
  bcc?: string[]
  subject: string
  contentType?: 'text' | 'html'
  content: string
  attachmentIds?: number[]
}

// ---------- 邮件列表查询参数 ----------

export interface MailListParams {
  accountId?: number
  folderId?: number
  keyword?: string
  read?: boolean
  /** 智能垃圾邮件标签筛选：normal / spam */
  spamLabel?: string
  /** 智能优先级标签筛选：high / low */
  priorityLabel?: string
  /** 智能风险等级筛选：high / medium / low */
  riskLevel?: string
  page?: number
  size?: number
}

export type MailListResponse = PaginatedData<MailSummary>

// ---------- 邮箱账号（对应后端 MailAccountResponse） ----------

export interface MailAccount {
  id: number
  userId: number
  emailAddress: string
  displayName: string | null
  smtpHost: string
  smtpPort: number
  smtpSsl: boolean
  imapHost: string
  imapPort: number | null
  imapSsl: boolean
  authUsername: string
  status: number
  lastSyncAt: string | null
}

// ---------- 邮箱账号创建/更新请求（对应后端 MailAccountRequest） ----------

export interface MailAccountRequest {
  emailAddress: string
  displayName?: string
  smtpHost: string
  smtpPort: number
  smtpSsl: boolean
  imapHost?: string
  imapPort?: number
  imapSsl: boolean
  authUsername: string
  authPassword: string
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
