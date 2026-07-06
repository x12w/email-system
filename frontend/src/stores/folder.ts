import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { FolderItem } from '@/types/folder'
import { getFolderList } from '@/api/folder'

/**
 * 文件夹状态管理。
 * 管理侧边栏文件夹列表及当前选中文件夹。
 */
export const useFolderStore = defineStore('folder', () => {
  const folderList = ref<FolderItem[]>([])
  const loading = ref(false)

  /** 当前选中的文件夹 ID */
  const currentFolderId = ref<number | undefined>(undefined)
  /** 当前选中的文件夹类型 */
  const currentFolderType = ref<string>('inbox')

  async function fetchFolders(): Promise<void> {
    loading.value = true
    try {
      folderList.value = await getFolderList()
      // 默认选中收件箱
      const inbox = folderList.value.find((f) => f.type === 'inbox')
      if (inbox && !currentFolderId.value) {
        currentFolderId.value = inbox.id
        currentFolderType.value = 'inbox'
      }
    } catch {
      folderList.value = []
    } finally {
      loading.value = false
    }
  }

  function setCurrentFolder(folderId: number | undefined, folderType?: string) {
    currentFolderId.value = folderId
    if (folderType) currentFolderType.value = folderType
  }

  function reset() {
    folderList.value = []
    currentFolderId.value = undefined
    currentFolderType.value = 'inbox'
    loading.value = false
  }

  return {
    folderList,
    loading,
    currentFolderId,
    currentFolderType,
    fetchFolders,
    setCurrentFolder,
    reset,
  }
})
