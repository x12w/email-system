import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { IntelligenceResult, PluginStatus, PushEvent, ThreatIndicator } from '@/types/mail'
import {
  getIntelligenceResult,
  analyzeMessage,
  listPlugins,
  listPushEvents,
  markPushEventRead,
  getThreats,
} from '@/api/intelligence'

/**
 * AI 智能分析状态管理。
 * 管理威胁指标、推送事件、插件状态及邮件分析结果。
 */
export const useIntelligenceStore = defineStore('intelligence', () => {
  // ---------- 威胁指标 ----------

  const threats = ref<ThreatIndicator[]>([])
  const threatsLoading = ref(false)

  async function fetchThreats(): Promise<void> {
    threatsLoading.value = true
    try {
      threats.value = await getThreats()
    } catch {
      threats.value = []
    } finally {
      threatsLoading.value = false
    }
  }

  // ---------- 推送事件 ----------

  const pushEvents = ref<PushEvent[]>([])
  const pushEventsLoading = ref(false)

  const unreadPushCount = computed(() =>
    pushEvents.value.filter((e) => !e.read).length,
  )

  async function fetchPushEvents(): Promise<void> {
    pushEventsLoading.value = true
    try {
      pushEvents.value = await listPushEvents()
    } catch {
      pushEvents.value = []
    } finally {
      pushEventsLoading.value = false
    }
  }

  async function markPushRead(id: number): Promise<void> {
    const event = pushEvents.value.find((e) => e.id === id)
    if (!event || event.read) return
    await markPushEventRead(id)
    event.read = true
  }

  // ---------- 插件状态 ----------

  const plugins = ref<PluginStatus[]>([])
  const pluginsLoading = ref(false)

  async function fetchPlugins(): Promise<void> {
    pluginsLoading.value = true
    try {
      plugins.value = await listPlugins()
    } catch {
      plugins.value = []
    } finally {
      pluginsLoading.value = false
    }
  }

  // ---------- 邮件分析结果缓存 ----------

  /** messageId → IntelligenceResult 的缓存映射 */
  const analysisCache = ref<Record<number, IntelligenceResult>>({})

  async function fetchAnalysis(messageId: number): Promise<IntelligenceResult | null> {
    try {
      const result = await getIntelligenceResult(messageId)
      analysisCache.value[messageId] = result
      return result
    } catch {
      return null
    }
  }

  async function triggerAnalyze(messageId: number): Promise<IntelligenceResult> {
    const result = await analyzeMessage(messageId)
    analysisCache.value[messageId] = result
    return result
  }

  function getCachedAnalysis(messageId: number): IntelligenceResult | undefined {
    return analysisCache.value[messageId]
  }

  return {
    threats,
    threatsLoading,
    fetchThreats,
    pushEvents,
    pushEventsLoading,
    unreadPushCount,
    fetchPushEvents,
    markPushRead,
    plugins,
    pluginsLoading,
    fetchPlugins,
    analysisCache,
    fetchAnalysis,
    triggerAnalyze,
    getCachedAnalysis,
  }
})
