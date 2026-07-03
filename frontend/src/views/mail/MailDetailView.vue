<template>
  <div class="mail-detail" v-loading="loading">
    <!-- 顶部操作栏 -->
    <header class="detail-header">
      <el-button text :icon="ArrowLeft" @click="router.back()">返回列表</el-button>
      <div class="detail-actions">
        <el-button :icon="RefreshRight" @click="toggleRead">
          {{ mail?.read ? '标记未读' : '标记已读' }}
        </el-button>
        <el-button :icon="ChatLineSquare" @click="goReply('reply')" :disabled="!mail || mail.draft">
          回复
        </el-button>
        <el-button :icon="ChatDotRound" @click="goReply('replyAll')" :disabled="!mail || mail.draft">
          回复全部
        </el-button>
        <el-button :icon="Share" @click="goReply('forward')" :disabled="!mail || mail.draft">
          转发
        </el-button>
        <el-button :icon="Delete" type="danger" plain @click="handleDelete">删除</el-button>
      </div>
    </header>

    <!-- 错误状态 -->
    <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon closable />

    <!-- 邮件内容 -->
    <article v-if="mail" class="mail-article">
      <!-- 标题 -->
      <h2 class="mail-subject-title">{{ mail.subject || '(无主题)' }}</h2>

      <!-- 元信息 -->
      <div class="mail-meta">
        <div class="meta-row">
          <span class="meta-label">发件人：</span>
          <span class="meta-value">{{ mail.fromName ? `${mail.fromName} <${mail.fromAddress}>` : mail.fromAddress }}</span>
        </div>
        <div class="meta-row" v-if="mail.to && mail.to.length">
          <span class="meta-label">收件人：</span>
          <span class="meta-value">{{ mail.to.join('; ') }}</span>
        </div>
        <div class="meta-row" v-if="mail.cc && mail.cc.length">
          <span class="meta-label">抄送：</span>
          <span class="meta-value">{{ mail.cc.join('; ') }}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">时间：</span>
          <span class="meta-value">{{ formatDateTime(mail.receivedAt || mail.sentAt) }}</span>
        </div>
      </div>

      <el-divider />

      <!-- 附件列表 -->
      <div v-if="mail.attachments && mail.attachments.length > 0" class="attachment-section">
        <h4 class="section-title">
          <el-icon><Paperclip /></el-icon>
          附件 ({{ mail.attachments.length }})
        </h4>
        <div class="attachment-list">
          <div
            v-for="att in mail.attachments"
            :key="att.id"
            class="attachment-item"
            @click="downloadAttachment(att.id, att.originalName)"
          >
            <el-icon :size="20"><Document /></el-icon>
            <span class="att-name">{{ att.originalName }}</span>
            <span class="att-size">{{ formatSize(att.sizeBytes) }}</span>
            <el-icon :size="16" color="#9ca3af"><Download /></el-icon>
          </div>
        </div>
        <el-divider />
      </div>

      <!-- 邮件正文 -->
      <div class="mail-body" v-html="mail.content || mail.preview || ''" />

      <!-- 正文为空 -->
      <el-empty v-if="!mail.content && !mail.preview" description="该邮件没有正文内容" :image-size="80" />

      <el-divider />

      <!-- AI 智能分析面板 -->
      <section class="ai-analysis-section">
        <div class="ai-analysis-header">
          <h4 class="section-title">
            <el-icon><Cpu /></el-icon>
            AI 智能分析
          </h4>
          <el-button
            size="small"
            type="primary"
            :loading="analyzing"
            @click="triggerAnalyze"
          >
            {{ intelligenceResult ? '重新分析' : '开始分析' }}
          </el-button>
        </div>

        <!-- 加载中 -->
        <div v-if="intelLoading" class="ai-loading">
          <el-icon class="is-loading" :size="20"><Loading /></el-icon>
          <span>正在加载分析结果...</span>
        </div>

        <!-- 空状态：未分析 -->
        <div v-else-if="!intelligenceResult" class="ai-empty">
          <span>该邮件尚未进行 AI 智能分析，点击上方按钮开始分析。</span>
        </div>

        <!-- 分析中（后端返回 processing 状态） -->
        <div v-else-if="intelligenceResult.spamLabel === 'processing'" class="ai-processing">
          <el-alert
            title="AI 分析任务正在排队或处理中，请稍后刷新"
            type="info"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 分析结果 -->
        <div v-else class="ai-results">
          <!-- 三列指标卡片 -->
          <div class="ai-metrics">
            <!-- 垃圾邮件判定 -->
            <div class="ai-metric-card">
              <span class="ai-metric-label">垃圾邮件判定</span>
              <el-tag
                :type="intelligenceResult.spamLabel === 'spam' ? 'danger' : 'success'"
                size="default"
                effect="dark"
              >
                {{ intelligenceResult.spamLabel === 'spam' ? '垃圾邮件' : '正常' }}
              </el-tag>
              <el-progress
                :percentage="Math.round(intelligenceResult.spamScore * 100)"
                :color="intelligenceResult.spamLabel === 'spam' ? '#dc2626' : '#16a34a'"
                :stroke-width="6"
              />
              <span class="ai-metric-score">置信度 {{ (intelligenceResult.spamScore * 100).toFixed(1) }}%</span>
            </div>

            <!-- 优先级判定 -->
            <div class="ai-metric-card">
              <span class="ai-metric-label">优先级判定</span>
              <el-tag
                :type="intelligenceResult.priorityLabel === 'high' ? 'warning' : 'info'"
                size="default"
                effect="dark"
              >
                {{ intelligenceResult.priorityLabel === 'high' ? '高优先级' : '低优先级' }}
              </el-tag>
              <el-progress
                :percentage="Math.round(intelligenceResult.priorityScore * 100)"
                :color="intelligenceResult.priorityLabel === 'high' ? '#d97706' : '#6b7280'"
                :stroke-width="6"
              />
              <span class="ai-metric-score">分数 {{ (intelligenceResult.priorityScore * 100).toFixed(1) }}%</span>
            </div>

            <!-- 风险等级 -->
            <div class="ai-metric-card">
              <span class="ai-metric-label">风险等级</span>
              <el-tag
                :type="riskLevelTagType(intelligenceResult.riskLevel)"
                size="default"
                effect="dark"
              >
                {{ riskLevelLabel(intelligenceResult.riskLevel) }}
              </el-tag>
              <el-progress
                :percentage="Math.round(intelligenceResult.riskScore * 100)"
                :color="riskLevelColor(intelligenceResult.riskLevel)"
                :stroke-width="6"
              />
              <span class="ai-metric-score">分数 {{ (intelligenceResult.riskScore * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <!-- 分析来源信息 -->
          <div class="ai-meta">
            <span>分析引擎：{{ intelligenceResult.pluginName }} v{{ intelligenceResult.pluginVersion }}</span>
            <span v-if="intelligenceResult.analyzedAt">分析时间：{{ formatDateTime(intelligenceResult.analyzedAt) }}</span>
          </div>

          <!-- 威胁项列表 -->
          <div v-if="intelligenceResult.threats && intelligenceResult.threats.length > 0" class="ai-threats">
            <h5 class="ai-threats-title">威胁项 ({{ intelligenceResult.threats.length }})</h5>
            <el-table
              :data="intelligenceResult.threats"
              size="small"
              class="threats-table"
            >
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="value" label="值" min-width="180" show-overflow-tooltip />
              <el-table-column label="风险等级" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="riskLevelTagType(row.riskLevel)" size="small" effect="plain">
                    {{ riskLevelLabel(row.riskLevel) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
            </el-table>
          </div>

          <!-- 无威胁项 -->
          <div v-else class="ai-no-threats">
            <span>未检测到威胁项</span>
          </div>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, RefreshRight, Delete, Paperclip, Document, Download, Cpu, Loading,
  ChatLineSquare, ChatDotRound, Share,
} from '@element-plus/icons-vue'
import {
  getMailDetail, markAsRead, markAsUnread, deleteMail,
  downloadAttachment as downloadAtt,
} from '@/api/mail'
import { getIntelligenceResult, analyzeMessage } from '@/api/intelligence'
import type { MailItem, IntelligenceResult } from '@/types/mail'

const route = useRoute()
const router = useRouter()

const mail = ref<MailItem | null>(null)
const loading = ref(false)
const errorMsg = ref('')

// AI 智能分析相关状态
const intelligenceResult = ref<IntelligenceResult | null>(null)
const intelLoading = ref(false)
const analyzing = ref(false)

async function loadDetail() {
  const id = Number(route.params.id)
  if (!id) {
    errorMsg.value = '无效的邮件 ID'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    mail.value = await getMailDetail(id)
    // 自动标记已读
    if (mail.value && !mail.value.read) {
      markAsRead(id).then(() => {
        if (mail.value) mail.value.read = true
      }).catch(() => {})
    }
    // 加载 AI 分析结果（不阻塞详情展示）
    loadIntelligence(id)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '加载失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
}

/** 加载 AI 智能分析结果 */
async function loadIntelligence(messageId: number) {
  intelLoading.value = true
  try {
    intelligenceResult.value = await getIntelligenceResult(messageId)
  } catch {
    // 分析结果可能不存在，静默处理
    intelligenceResult.value = null
  } finally {
    intelLoading.value = false
  }
}

/** 触发 AI 分析 */
async function triggerAnalyze() {
  if (!mail.value) return
  analyzing.value = true
  try {
    intelligenceResult.value = await analyzeMessage(mail.value.id)
    ElMessage.success('AI 分析完成')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '分析失败'
    ElMessage.error(msg)
  } finally {
    analyzing.value = false
  }
}

/** 风险等级 → el-tag type */
function riskLevelTagType(level: string): 'danger' | 'warning' | 'info' {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}

/** 风险等级 → 中文标签 */
function riskLevelLabel(level: string): string {
  if (level === 'high') return '高风险'
  if (level === 'medium') return '中风险'
  if (level === 'low') return '低风险'
  return level
}

/** 风险等级 → 进度条颜色 */
function riskLevelColor(level: string): string {
  if (level === 'high') return '#dc2626'
  if (level === 'medium') return '#d97706'
  return '#16a34a'
}

async function toggleRead() {
  if (!mail.value) return
  const id = mail.value.id
  try {
    if (mail.value.read) {
      await markAsUnread(id)
      mail.value.read = false
      ElMessage.success('已标记为未读')
    } else {
      await markAsRead(id)
      mail.value.read = true
      ElMessage.success('已标记为已读')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDelete() {
  if (!mail.value) return
  try {
    await ElMessageBox.confirm('确认删除该邮件？', '删除确认', { type: 'warning' })
    await deleteMail(mail.value.id)
    ElMessage.success('已删除')
    router.push('/')
  } catch {
    // 用户取消
  }
}

/** 跳转到写邮件页，携带回复/转发上下文 */
function goReply(mode: 'reply' | 'replyAll' | 'forward') {
  if (!mail.value) return
  router.push(`/compose?replyId=${mail.value.id}&mode=${mode}`)
}

async function downloadAttachment(id: number, fileName: string) {
  try {
    const blob = await downloadAtt(id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  return new Date(isoString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.mail-detail {
  max-width: 860px;
  margin: 0 auto;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.detail-actions {
  display: flex;
  gap: 8px;
}

.mail-article {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px 28px;
}

.mail-subject-title {
  margin: 0 0 16px;
  font-size: 20px;
  color: #111827;
}

.mail-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.meta-row {
  display: flex;
}
.meta-label {
  color: #6b7280;
  min-width: 64px;
  flex-shrink: 0;
}
.meta-value {
  color: #374151;
  word-break: break-all;
}

.attachment-section {
  margin-bottom: 0;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 10px;
  font-size: 14px;
  color: #374151;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid #f3f4f6;
}
.attachment-item:hover {
  background: #f9fafb;
  border-color: #e5e7eb;
}
.att-name {
  flex: 1;
  font-size: 13px;
  color: #2563eb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.att-size {
  font-size: 12px;
  color: #9ca3af;
}

.mail-body {
  line-height: 1.7;
  color: #1f2937;
  word-break: break-word;
}
/* 邮件正文中的图片和表格不做溢出 */
.mail-body :deep(img) {
  max-width: 100%;
}
.mail-body :deep(table) {
  max-width: 100%;
}

/* AI 智能分析面板 */
.ai-analysis-section {
  margin-top: 0;
}

.ai-analysis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.ai-loading,
.ai-empty,
.ai-processing,
.ai-no-threats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #9ca3af;
  font-size: 13px;
}

.ai-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 14px;
}

.ai-metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  background: #f9fafb;
  border: 1px solid #f3f4f6;
  border-radius: 8px;
}

.ai-metric-label {
  color: #6b7280;
  font-size: 12px;
}

.ai-metric-score {
  color: #9ca3af;
  font-size: 12px;
  text-align: right;
}

.ai-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 14px;
  color: #9ca3af;
  font-size: 12px;
}

.ai-threats-title {
  margin: 0 0 8px;
  font-size: 13px;
  color: #374151;
}

.threats-table {
  width: 100%;
}

@media (max-width: 640px) {
  .ai-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
