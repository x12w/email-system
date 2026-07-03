import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ContactItem } from '@/types/contact'
import { getContactList } from '@/api/contact'

/**
 * 联系人状态管理。
 * 缓存联系人列表，供撰写邮件自动补全等场景使用。
 */
export const useContactStore = defineStore('contact', () => {
  const contacts = ref<ContactItem[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  async function fetchContacts(keyword?: string): Promise<void> {
    // 如果已加载且无搜索关键词，使用缓存
    if (loaded.value && !keyword) return

    loading.value = true
    try {
      contacts.value = await getContactList(keyword)
      if (!keyword) loaded.value = true
    } catch {
      contacts.value = []
    } finally {
      loading.value = false
    }
  }

  function reset() {
    contacts.value = []
    loaded.value = false
    loading.value = false
  }

  return {
    contacts,
    loading,
    loaded,
    fetchContacts,
    reset,
  }
})
