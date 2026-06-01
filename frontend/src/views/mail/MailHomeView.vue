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
          <el-option label="全部" :value="undefined" />
          <el-option label="未读" :value="0" />
          <el-option label="已读" :value="1" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" @click="router.push('/compose')">
          <el-icon><Edit /></el-icon>
          写邮件
        </el-button>
        <el-button :disabled="!selectedIds.length" @click="batchMarkRead">
          <el-icon><Check /></el-icon>
          标记已读
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
          <el-icon v-if="row.starFlag" color="#f59e0b" :size="14"><StarFilled /></el-icon>
          <el-icon v-else color="#d1d5db" :size="14"><Star /></el-icon>
        </template>
      </el-table-column>

      <el-table-column label="发件人" width="160">
        <template #default="{ row }">
          <span class="mail-sender" :class="{ 'font-bold': !row.readFlag }">
            {{ row.fromName || row.fromAddress }}
          </span>
        </template>
      </el-table-column>

      <el-table-column label="主题" min-width="240">
        <template #default="{ row }">
          <div class="mail-subject-cell">
            <span class="mail-subject" :class="{ 'font-bold': !row.readFlag }">
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

      <el-table-column label="时间" width="150" align="right">
        <template #default="{ row }">
          <span class="mail-time">{{ formatTime(row.receivedAt || row.sentAt) }}</span>
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
  Search, Edit, Check, Delete, StarFilled, Star, Paperclip,
} from '@element-plus/icons-vue'
import { markAsRead, deleteMail } from '@/api/mail'
import { useMailStore } from '@/stores/mail'

const router = useRouter()
const mailStore = useMailStore()

const tableRef = ref<InstanceType<typeof ElTable>>()
const keyword = ref('')
const readFilter = ref<number | undefined>(undefined)
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
    readFilter.value = undefined
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

function onReadFilterChange(value: number | undefined) {
  mailStore.setFilters({ read: value })
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

function openDetail(row: { id: number; readFlag: number }) {
  // 未读邮件先标记已读
  if (!row.readFlag) {
    markAsRead(row.id).catch(() => {})
  }
  router.push(`/mail/${row.id}`)
}

// ---------- 工具函数 ----------

function rowClassName({ row }: { row: { readFlag: number } }) {
  return row.readFlag ? '' : 'row-unread'
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
