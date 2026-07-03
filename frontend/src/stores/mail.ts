import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MailSummary, MailListParams, MailAccount, SendMailRequest } from '@/types/mail'
import { getMailList, getMailAccounts, saveDraft, sendMail } from '@/api/mail'

export const useMailStore = defineStore('mail', () => {
  const mailList = ref<MailSummary[]>([])
  const currentMail = ref<MailSummary | null>(null)
  const total = ref(0)
  const loading = ref(false)

  // 当前激活的文件夹（用于侧边栏高亮）
  const currentFolderId = ref<number | undefined>(undefined)
  const currentFolderType = ref<string>('inbox')

  // 邮箱账号列表（用于发件人选择）
  const accounts = ref<MailAccount[]>([])
  const accountsLoading = ref(false)

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

  // ---------- 邮箱账号 ----------

  async function fetchAccounts(): Promise<void> {
    accountsLoading.value = true
    try {
      accounts.value = await getMailAccounts()
    } catch {
      accounts.value = []
    } finally {
      accountsLoading.value = false
    }
  }

  // ---------- 发送与草稿 ----------

  let sending = ref(false)

  /**
   * 发送邮件
   */
  async function doSendMail(data: SendMailRequest): Promise<void> {
    sending.value = true
    try {
      await sendMail(data)
    } finally {
      sending.value = false
    }
  }

  /**
   * 保存草稿，返回草稿 ID
   */
  async function doSaveDraft(data: SendMailRequest): Promise<number | null> {
    try {
      const result = await saveDraft(data)
      return result?.id ?? null
    } catch {
      return null
    }
  }

  return {
    mailList,
    currentMail,
    total,
    loading,
    filters,
    currentFolderId,
    currentFolderType,
    accounts,
    accountsLoading,
    sending,
    hasMore,
    currentPage,
    pageSize,
    setFilters,
    setCurrentFolder,
    resetMailList,
    fetchMailList,
    goToPage,
    fetchAccounts,
    doSendMail,
    doSaveDraft,
  }
})
