import request from '@/utils/request'
import type {
  IntelligenceResult,
  PluginStatus,
  PushEvent,
  ThreatIndicator,
} from '@/types/mail'

/**
 * 触发 AI 分析指定邮件。
 * POST /api/intelligence/messages/{id}/analyze
 */
export function analyzeMessage(id: number): Promise<IntelligenceResult> {
  return request.post(`/intelligence/messages/${id}/analyze`)
}

/**
 * 获取指定邮件的 AI 分析结果。
 * GET /api/intelligence/messages/{id}
 */
export function getIntelligenceResult(id: number): Promise<IntelligenceResult> {
  return request.get(`/intelligence/messages/${id}`)
}

/**
 * 获取智能分析插件列表。
 * GET /api/intelligence/plugins
 */
export function listPlugins(): Promise<PluginStatus[]> {
  return request.get('/intelligence/plugins')
}

/**
 * 获取推送事件列表。
 * GET /api/intelligence/push-events
 */
export function listPushEvents(): Promise<PushEvent[]> {
  return request.get('/intelligence/push-events')
}

/**
 * 标记推送事件为已读。
 * PUT /api/intelligence/push-events/{id}/read
 */
export function markPushEventRead(id: number): Promise<PushEvent> {
  return request.put(`/intelligence/push-events/${id}/read`)
}

/**
 * 获取威胁指标列表。
 * GET /api/intelligence/threats
 */
export function getThreats(): Promise<ThreatIndicator[]> {
  return request.get('/intelligence/threats')
}
