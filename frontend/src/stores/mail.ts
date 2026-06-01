import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MailItem, MailListParams } from '@/types/mail'
import { getMailList } from '@/api/mail'

export const useMailStore = defineStore('mail', () => {
  const mailList = ref<MailItem[]>([])
  const currentMail = ref<MailItem | null>(null)
  const total = ref(0)
  const loading = ref(false)

  // 当前激活的文件夹（用于侧边栏高亮）
  const currentFolderId = ref<number | undefined>(undefined)
  const currentFolderType = ref<string>('inbox')

  const filters = ref<MailListParams>({
    page: 1,
    size: 20,
  })

  const hasMore = computed(() => mailList.value.length < total.value)
  const currentPage = computed(() => filters.value.page || 1)
  const pageSize = computed(() => filters.value.size || 20)

  function setFilters(partial: Partial<MailListParams>) {
    filters.value = { ...filters.value, ...partial }
    // 修改筛选条件时重置页码
    if (partial.folderId !== undefined || partial.keyword !== undefined || partial.read !== undefined) {
      filters.value.page = 1
    }
  }

  function setCurrentFolder(folderId: number | undefined, folderType?: string) {
    currentFolderId.value = folderId
    if (folderType) currentFolderType.value = folderType
    setFilters({ folderId })
  }

  function resetMailList() {
    mailList.value = []
    total.value = 0
    filters.value.page = 1
  }

  /**
   * 拉取邮件列表
   */
  async function fetchMailList(): Promise<void> {
    loading.value = true
    try {
      const res = await getMailList({ ...filters.value })
      mailList.value = res.records
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换页码
   */
  async function goToPage(page: number): Promise<void> {
    setFilters({ page })
    await fetchMailList()
  }

  return {
    mailList,
    currentMail,
    total,
    loading,
    filters,
    currentFolderId,
    currentFolderType,
    hasMore,
    currentPage,
    pageSize,
    setFilters,
    setCurrentFolder,
    resetMailList,
    fetchMailList,
    goToPage,
  }
})
