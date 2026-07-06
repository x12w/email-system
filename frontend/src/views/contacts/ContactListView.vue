<template>
  <div class="contact-list-page">
    <header class="page-header">
      <h2>通讯录</h2>
      <div class="header-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索姓名或邮箱..."
          :prefix-icon="Search"
          clearable
          class="search-input"
          @input="onSearchInput"
          @clear="loadContacts"
        />
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增联系人</el-button>
      </div>
    </header>

    <!-- 联系人表格 -->
    <el-table
      v-loading="loading"
      :data="filteredContacts"
      row-key="id"
      stripe
      class="contact-table"
    >
      <el-table-column prop="name" label="姓名" min-width="120" />
      <el-table-column prop="emailAddress" label="邮箱" min-width="200" />
      <el-table-column prop="phone" label="电话" width="140">
        <template #default="{ row }">
          {{ row.phone || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="160">
        <template #default="{ row }">
          {{ row.remark || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="primary" @click="openEditDialog(row)">编辑</el-button>
          <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 空状态 -->
    <el-empty v-if="!loading && filteredContacts.length === 0" description="暂无联系人" />

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑联系人' : '新增联系人'"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入姓名" maxlength="50" />
        </el-form-item>
        <el-form-item label="邮箱" prop="emailAddress">
          <el-input v-model="formData.emailAddress" placeholder="请输入邮箱地址" maxlength="100" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入电话号码（选填）" maxlength="30" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="formData.remark"
            type="textarea"
            placeholder="备注信息（选填）"
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { getContactList, createContact, updateContact, deleteContact } from '@/api/contact'
import type { ContactItem, ContactRequest } from '@/types/contact'

// ---------- 列表数据 ----------

const contacts = ref<ContactItem[]>([])
const loading = ref(false)
const keyword = ref('')
let searchTimer: ReturnType<typeof setTimeout> | undefined

// 前端搜索过滤（后端 keyword 参数也做服务端过滤，这里做即时前端过滤优化）
const filteredContacts = computed(() => {
  if (!keyword.value.trim()) return contacts.value
  const kw = keyword.value.trim().toLowerCase()
  return contacts.value.filter(
    (c) => c.name.toLowerCase().includes(kw) || c.emailAddress.toLowerCase().includes(kw),
  )
})

async function loadContacts() {
  loading.value = true
  try {
    contacts.value = await getContactList()
  } catch {
    contacts.value = []
    ElMessage.error('加载联系人失败')
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  clearTimeout(searchTimer)
  // 前端即时过滤，不需要额外处理
}

// ---------- 表单逻辑 ----------

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const defaultFormData: ContactRequest = {
  name: '',
  emailAddress: '',
  phone: '',
  remark: '',
}

const formData = ref<ContactRequest>({ ...defaultFormData })

const formRules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  emailAddress: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
}

function resetForm() {
  formData.value = { ...defaultFormData }
  isEditing.value = false
  editingId.value = null
  formRef.value?.resetFields()
}

function openCreateDialog() {
  resetForm()
  dialogVisible.value = true
}

function openEditDialog(row: ContactItem) {
  isEditing.value = true
  editingId.value = row.id
  formData.value = {
    name: row.name,
    emailAddress: row.emailAddress,
    phone: row.phone || '',
    remark: row.remark || '',
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEditing.value && editingId.value !== null) {
      await updateContact(editingId.value, formData.value)
      ElMessage.success('联系人已更新')
    } else {
      await createContact(formData.value)
      ElMessage.success('联系人已创建')
    }
    dialogVisible.value = false
    await loadContacts()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

// ---------- 删除 ----------

async function handleDelete(row: ContactItem) {
  try {
    await ElMessageBox.confirm(`确认删除联系人 "${row.name}"？`, '删除确认', { type: 'warning' })
    await deleteContact(row.id)
    ElMessage.success('已删除')
    await loadContacts()
  } catch {
    // 用户取消
  }
}

// ---------- 初始化 ----------

onMounted(() => {
  loadContacts()
})
</script>

<style scoped>
.contact-list-page {
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 240px;
}

.contact-table {
  margin-bottom: 20px;
}
</style>
