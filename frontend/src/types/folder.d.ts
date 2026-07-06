// ---------- 文件夹（对应后端 FolderResponse） ----------

export interface FolderItem {
  id: number
  accountId: number
  name: string
  remoteName: string | null
  /** 文件夹类型：inbox / sent / draft / trash / spam / custom */
  type: string
  unreadCount: number
  totalCount: number
}

// ---------- 同步文件夹响应 ----------

export interface SyncFolderResult {
  status: string
}
