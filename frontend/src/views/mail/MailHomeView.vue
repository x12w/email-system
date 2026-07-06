<template>
  <div class="mail-home">
    <!-- 顶部工具栏 -->
    <header class="mail-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="keyword"
          placeholder="搜索邮件主题、发件人..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @input="onSearchInput"
          @clear="onSearchClear"
        />
        <el-select
          v-model="readFilter"
          placeholder="读取状态"
          clearable
          class="read-filter"
          @change="onReadFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="未读" :value="false" />
          <el-option label="已读" :value="true" />
        </el-select>
        <el-select
          v-model="spamLabelFilter"
          placeholder="垃圾邮件"
          clearable
          class="smart-filter"
          @change="onSpamLabelFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="正常" value="normal" />
          <el-option label="垃圾邮件" value="spam" />
        </el-select>
        <el-select
          v-model="priorityLabelFilter"
          placeholder="优先级"
          clearable
          class="smart-filter"
          @change="onPriorityLabelFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="高" value="high" />
          <el-option label="低" value="low" />
        </el-select>
        <el-select
          v-model="riskLevelFilter"
          placeholder="风险等级"
          clearable
          class="smart-filter"
          @change="onRiskLevelFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option label="高" value="high" />
          <el-option label="中" value="medium" />
          <el-option label="低" value="low" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button :icon="Refresh" @click="loadMailList" :loading="mailStore.loading">刷新</el-button>
        <el-button type="primary" @click="router.push('/compose')">
          <el-icon><Edit /></el-icon>
          写邮件
        </el-button>
        <el-button :disabled="!selectedIds.length" @click="batchMarkRead">
          <el-icon><Check /></el-icon>
          标记已读
        </el-button>
        <el-button :disabled="!selectedIds.length" @click="batchMarkUnread">
          <el-icon><Close /></el-icon>
          标记未读
        </el-button>
        <el-button :disabled="!selectedIds.length" type="danger" plain @click="batchDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </header>

    <!-- 邮件列表 -->
    <el-table
      ref="tableRef"
      v-loading="mailStore.loading"
      :data="mailStore.mailList"
      row-key="id"
      :row-class-name="rowClassName"
      highlight-current-row
      stripe
      class="mail-table"
      @row-click="openDetail"
      @selection-change="onSelectionChange"
    >
      <el-table-column type="selection" width="40" />

      <el-table-column width="36" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.starred" color="#f59e0b" :size="14"><StarFilled /></el-icon>
          <el-icon v-else color="#d1d5db" :size="14"><Star /></el-icon>
        </template>
      </el-table-column>

      <!-- 发件人 -->
      <el-table-column label="发件人" width="160">
        <template #default="{ row }">
          <span class="mail-sender" :class="{ 'font-bold': !row.read }">
            {{ row.fromName || row.fromAddress }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="主题" min-width="240">
        <template #default="{ row }">
          <div class="mail-subject-cell">
            <span class="mail-subject" :class="{ 'font-bold': !row.read }">
              {{ row.subject || '(无主题)' }}
            </span>
            <span class="mail-preview">{{ row.preview }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column width="28" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.attachmentCount > 0" :size="14" color="#9ca3af">
            <Paperclip />
          </el-icon>
        </template>
      </el-table-column>

      <!-- 智能标签：垃圾邮件 -->
      <el-table-column label="垃圾邮件" width="90" align="center">
        <template #default="{ row }">
          <el-tag
            v-if="row.spamLabel"
            :type="row.spamLabel === 'spam' ? 'danger' : 'success'"
            size="small"
            effect="plain"
          >
            {{ row.spamLabel === 'spam' ? '垃圾' : '正常' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 智能标签：优先级 -->
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag
            v-if="row.priorityLabel"
            :type="row.priorityLabel === 'high' ? 'warning' : 'info'"
            size="small"
            effect="plain"
          >
            {{ row.priorityLabel === 'high' ? '高' : '低' }}
          </el-tag>
        </template>
      </el-table-column>

      <!-- 智能标签：风险等级 -->
      <el-table-column label="风险" width="80" align="center">
        <template #default="{ row }">
          <el-tag
            v-if="row.riskLevel"
            :type="riskTagType(row.riskLevel)"
            size="small"
            effect="plain"
          >
            {{ row.riskLevel === 'high' ? '高' : row.riskLevel === 'medium' ? '中' : '低' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="时间" width="150" align="right">
        <template #default="{ row }">
          <span class="mail-time">{{ formatTime(row.receivedAt) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="80" align="center" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="danger" @click.stop="handleDelete(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 空状态 -->
    <el-empty v-if="!mailStore.loading && mailStore.mailList.length === 0" description="暂无邮件" />

    <!-- 分页 -->
    <div v-if="mailStore.total > 0" class="mail-pagination">
      <el-pagination
        v-model:current-page="currentPageModel"
        :page-size="mailStore.pageSize"
        :total="mailStore.total"
        layout="total, prev, pager, next"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTable } from 'element-plus'
import {
  Search, Edit, Check, Close, Delete, Refresh, StarFilled, Star, Paperclip,
} from '@element-plus/icons-vue'
import { markAsRead, markAsUnread, deleteMail } from '@/api/mail'
import { useMailStore } from '@/stores/mail'

const router = useRouter()
const mailStore = useMailStore()

const tableRef = ref<InstanceType<typeof ElTable>>()
const keyword = ref('')
const readFilter = ref<boolean | string>('')
const spamLabelFilter = ref<string>('')
const priorityLabelFilter = ref<string>('')
const riskLevelFilter = ref<string>('')
const currentPageModel = ref(mailStore.currentPage)
const selectedIds = ref<number[]>([])

// 搜索防抖计时器
let searchTimer: ReturnType<typeof setTimeout>

// ---------- 数据加载 ----------

async function loadMailList() {
  await mailStore.fetchMailList()
  currentPageModel.value = mailStore.currentPage
}

// 监听文件夹切换 → 自动加载
watch(
  () => mailStore.currentFolderId,
  () => {
    keyword.value = ''
    readFilter.value = ''
    loadMailList()
  },
)

onMounted(() => {
  loadMailList()
})

// ---------- 搜索与筛选 ----------

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    mailStore.setFilters({ keyword: keyword.value || undefined })
    loadMailList()
  }, 400)
}

function onSearchClear() {
  mailStore.setFilters({ keyword: undefined })
  loadMailList()
}

function onReadFilterChange(value: boolean | string) {
  mailStore.setFilters({ read: value === '' ? undefined : (value as boolean) })
  loadMailList()
}

function onSpamLabelFilterChange(value: string) {
  mailStore.setFilters({ spamLabel: value || undefined })
  loadMailList()
}

function onPriorityLabelFilterChange(value: string) {
  mailStore.setFilters({ priorityLabel: value || undefined })
  loadMailList()
}

function onRiskLevelFilterChange(value: string) {
  mailStore.setFilters({ riskLevel: value || undefined })
  loadMailList()
}

// ---------- 分页 ----------

function onPageChange(page: number) {
  mailStore.goToPage(page)
  currentPageModel.value = page
}

// ---------- 操作 ----------

function onSelectionChange(rows: { id: number }[]) {
  selectedIds.value = rows.map((r) => r.id)
}

async function batchMarkRead() {
  if (selectedIds.value.length === 0) return
  try {
    await Promise.all(selectedIds.value.map((id) => markAsRead(id)))
    ElMessage.success(`已标记 ${selectedIds.value.length} 封邮件为已读`)
    loadMailList()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function batchMarkUnread() {
  if (selectedIds.value.length === 0) return
  try {
    await Promise.all(selectedIds.value.map((id) => markAsUnread(id)))
    ElMessage.success(`已标记 ${selectedIds.value.length} 封邮件为未读`)
    loadMailList()
  } catch {
    ElMessage.error('操作失败')
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedIds.value.length} 封邮件？`,
      '删除确认',
      { type: 'warning' },
    )
    await Promise.all(selectedIds.value.map((id) => deleteMail(id)))
    ElMessage.success('删除成功')
    loadMailList()
  } catch {
    // 用户取消
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确认删除该邮件？', '删除确认', { type: 'warning' })
    await deleteMail(id)
    ElMessage.success('已删除')
    loadMailList()
  } catch {
    // 用户取消
  }
}

function openDetail(row: { id: number; read: boolean; draft: boolean }) {
  // 草稿邮件 → 跳转写邮件页编辑
  if (row.draft) {
    router.push(`/compose?draftId=${row.id}`)
    return
  }
  // 未读邮件先标记已读
  if (!row.read) {
    markAsRead(row.id).catch(() => {})
  }
  router.push(`/mail/${row.id}`)
}

// ---------- 工具函数 ----------

function rowClassName({ row }: { row: { read: boolean } }) {
  return row.read ? '' : 'row-unread'
}

function formatTime(isoString: string | null): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

/** 根据风险等级返回 el-tag 的 type */
function riskTagType(level: string): 'danger' | 'warning' | 'info' {
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'info'
}
</script>

<style scoped>
.mail-home {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mail-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 280px;
}
.read-filter {
  width: 110px;
}
.smart-filter {
  width: 110px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mail-table {
  flex: 1;
}

.mail-sender {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.mail-subject-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.mail-subject {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mail-preview {
  font-size: 12px;
  color: #9ca3af;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mail-time {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
}

.font-bold {
  font-weight: 600;
}

.mail-pagination {
  display: flex;
  justify-content: center;
  padding: 16px 0 0;
}
</style>
