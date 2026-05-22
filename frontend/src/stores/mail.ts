import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { MailItem, MailListParams } from '@/types/mail'

export const useMailStore = defineStore('mail', () => {
  const mailList = ref<MailItem[]>([])
  const currentMail = ref<MailItem | null>(null)
  const total = ref(0)
  const loading = ref(false)

  const filters = ref<MailListParams>({
    page: 1,
    size: 20,
  })

  const hasMore = computed(() => mailList.value.length < total.value)

  function setFilters(partial: Partial<MailListParams>) {
    filters.value = { ...filters.value, ...partial }
  }

  function resetMailList() {
    mailList.value = []
    total.value = 0
    filters.value.page = 1
  }

  return {
    mailList,
    currentMail,
    total,
    loading,
    filters,
    hasMore,
    setFilters,
    resetMailList,
  }
})
