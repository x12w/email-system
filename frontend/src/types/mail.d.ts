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
