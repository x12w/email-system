<template>
  <div class="mail-detail" v-loading="loading">
    <!-- 顶部操作栏 -->
    <header class="detail-header">
      <el-button text :icon="ArrowLeft" @click="router.back()">返回列表</el-button>
      <div class="detail-actions">
        <el-button :icon="RefreshRight" @click="toggleRead">
          {{ mail?.read ? '标记未读' : '标记已读' }}
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
    </article>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, RefreshRight, Delete, Paperclip, Document, Download,
} from '@element-plus/icons-vue'
import { getMailDetail, markAsRead, markAsUnread, deleteMail, downloadAttachment as downloadAtt } from '@/api/mail'
import type { MailItem } from '@/types/mail'

const route = useRoute()
const router = useRouter()

const mail = ref<MailItem | null>(null)
const loading = ref(false)
const errorMsg = ref('')

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
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '加载失败'
    errorMsg.value = msg
  } finally {
    loading.value = false
  }
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
</style>
