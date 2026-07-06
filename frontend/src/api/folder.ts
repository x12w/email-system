import request from '@/utils/request'
import type { FolderItem, SyncFolderResult } from '@/types/folder'

/**
 * 获取文件夹列表（后端不需要 accountId 参数）。
 */
export function getFolderList(): Promise<FolderItem[]> {
  return request.get('/folders')
}

/**
 * 同步远程文件夹（后端无请求体，返回 { status: "queued" }）。
 */
export function syncFolders(): Promise<SyncFolderResult> {
  return request.post('/folders/sync')
}
