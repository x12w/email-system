import request from '@/utils/request'
import type { FolderItem, SyncFolderRequest } from '@/types/folder'

export function getFolderList(accountId?: number): Promise<FolderItem[]> {
  return request.get('/folders', { params: accountId !== undefined ? { accountId } : {} })
}

export function syncFolders(accountId: number): Promise<FolderItem[]> {
  return request.post('/folders/sync', { accountId } as SyncFolderRequest)
}
