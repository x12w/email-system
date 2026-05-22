export interface FolderItem {
  id: number
  userId: number
  accountId: number
  name: string
  remoteName: string | null
  type: 'inbox' | 'sent' | 'draft' | 'trash' | 'spam' | 'custom'
  unreadCount: number
  totalCount: number
  sortOrder: number
}

export interface SyncFolderRequest {
  accountId: number
}
