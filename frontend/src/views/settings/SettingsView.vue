<template>
  <div class="settings-page">
    <!-- 邮箱账号管理 -->
    <section class="settings-section">
      <header class="section-header">
        <h3>邮箱账号</h3>
        <div class="header-actions">
          <el-button :icon="Refresh" :loading="syncingFolders" @click="handleSyncFolders">
            同步文件夹
          </el-button>
          <el-button :icon="Message" :loading="processingMail" @click="openProcessDialog">
            手动接收邮件
          </el-button>
          <el-button type="primary" :icon="Plus" @click="openCreateDialog">新增账号</el-button>
        </div>
      </header>

      <p class="section-desc">管理已绑定的邮箱账号，配置 SMTP 发送和 IMAP 接收。</p>

      <!-- 账号表格 -->
      <el-table
        v-loading="loading"
        :data="accounts"
        row-key="id"
        stripe
        class="account-table"
      >
        <el-table-column prop="emailAddress" label="邮箱地址" min-width="180" />
        <el-table-column prop="displayName" label="显示名称" width="120">
          <template #default="{ row }">
            {{ row.displayName || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="SMTP" width="200">
          <template #default="{ row }">
            {{ row.smtpHost }}:{{ row.smtpPort }}
            <el-tag :type="row.smtpSsl ? 'success' : 'info'" size="small" class="ssl-tag">
              {{ row.smtpSsl ? 'SSL' : 'PLAIN' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="IMAP" width="200">
          <template #default="{ row }">
            <template v-if="row.imapHost">
              {{ row.imapHost }}:{{ row.imapPort }}
              <el-tag :type="row.imapSsl ? 'success' : 'info'" size="small" class="ssl-tag">
                {{ row.imapSsl ? 'SSL' : 'PLAIN' }}
              </el-tag>
            </template>
            <span v-else class="text-muted">未配置</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'" size="small">
              {{ row.status === 1 ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最后同步" width="160">
          <template #default="{ row }">
            {{ row.lastSyncAt ? formatDateTime(row.lastSyncAt) : '未同步' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" type="primary" :loading="testingId === row.id" @click="handleTest(row.id)">
              测试连接
            </el-button>
            <el-button text size="small" type="primary" @click="openEditDialog(row)">编辑</el-button>
            <el-button text size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && accounts.length === 0" description="暂无邮箱账号，请新增" :image-size="80" />
    </section>

    <!-- 手动接收邮件弹窗 -->
    <el-dialog
      v-model="processDialogVisible"
      title="手动接收邮件"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetProcessForm"
    >
      <el-form ref="processFormRef" :model="processForm" :rules="processFormRules" label-width="100px">
        <el-form-item label="发件账号" prop="accountId">
          <el-select
            v-model="processForm.accountId"
            placeholder="选择接收账号"
            style="width: 100%"
          >
            <el-option
              v-for="acc in accounts"
              :key="acc.id"
              :label="`${acc.displayName || ''} <${acc.emailAddress}>`"
              :value="acc.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="发件人" prop="fromAddress">
          <el-input v-model="processForm.fromAddress" placeholder="sender@example.com" />
        </el-form-item>
        <el-form-item label="邮件UID" prop="messageUid">
          <el-input v-model="processForm.messageUid" placeholder="邮件唯一标识" />
        </el-form-item>
        <el-form-item label="主题" prop="subject">
          <el-input v-model="processForm.subject" placeholder="邮件主题" />
        </el-form-item>
        <el-form-item label="正文" prop="content">
          <el-input
            v-model="processForm.content"
            type="textarea"
            :rows="6"
            placeholder="邮件正文内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="processingMail" @click="handleProcessMail">接收并分析</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑邮箱账号' : '新增邮箱账号'"
      width="560px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="邮箱地址" prop="emailAddress">
          <el-input v-model="formData.emailAddress" placeholder="例如 user@example.com" maxlength="100" />
        </el-form-item>
        <el-form-item label="显示名称" prop="displayName">
          <el-input v-model="formData.displayName" placeholder="发送邮件时的显示名称（选填）" maxlength="50" />
        </el-form-item>

        <el-divider content-position="left">SMTP 发送配置</el-divider>

        <el-form-item label="SMTP 服务器" prop="smtpHost">
          <el-input v-model="formData.smtpHost" placeholder="例如 smtp.example.com" maxlength="100" />
        </el-form-item>
        <el-form-item label="SMTP 端口" prop="smtpPort">
          <el-input-number v-model="formData.smtpPort" :min="1" :max="65535" placeholder="465" />
        </el-form-item>
        <el-form-item label="SMTP SSL">
          <el-switch v-model="formData.smtpSsl" />
          <span class="switch-hint">{{ formData.smtpSsl ? 'SSL/TLS 加密' : '不加密' }}</span>
        </el-form-item>

        <el-divider content-position="left">IMAP 接收配置</el-divider>

        <el-form-item label="IMAP 服务器">
          <el-input v-model="formData.imapHost" placeholder="例如 imap.example.com（选填）" maxlength="100" />
        </el-form-item>
        <el-form-item label="IMAP 端口">
          <el-input-number v-model="formData.imapPort" :min="1" :max="65535" placeholder="993" />
        </el-form-item>
        <el-form-item label="IMAP SSL">
          <el-switch v-model="formData.imapSsl" />
          <span class="switch-hint">{{ formData.imapSsl ? 'SSL/TLS 加密' : '不加密' }}</span>
        </el-form-item>

        <el-divider content-position="left">认证信息</el-divider>

        <el-form-item label="认证用户名" prop="authUsername">
          <el-input v-model="formData.authUsername" placeholder="邮箱账号或认证用户名" maxlength="100" />
        </el-form-item>
        <el-form-item :label="isEditing ? '新密码' : '密码'" :prop="isEditing ? '' : 'authPassword'">
          <el-input
            v-model="formData.authPassword"
            type="password"
            show-password
            :placeholder="isEditing ? '留空则不修改密码' : '请输入邮箱密码或授权码'"
            maxlength="100"
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { Plus, Refresh, Message } from '@element-plus/icons-vue'
import {
  getMailAccounts,
  createMailAccount,
  updateMailAccount,
  deleteMailAccount,
  testMailAccount,
  processMail,
} from '@/api/mail'
import { syncFolders } from '@/api/folder'
import type { MailAccount, MailAccountRequest, ProcessMailRequest } from '@/types/mail'

// ---------- 列表数据 ----------

const accounts = ref<MailAccount[]>([])
const loading = ref(false)
const syncingFolders = ref(false)
const testingId = ref<number | null>(null)

async function loadAccounts() {
  loading.value = true
  try {
    accounts.value = await getMailAccounts()
  } catch {
    accounts.value = []
    ElMessage.error('加载邮箱账号失败')
  } finally {
    loading.value = false
  }
}

// ---------- 同步文件夹 ----------

async function handleSyncFolders() {
  syncingFolders.value = true
  try {
    const result = await syncFolders()
    ElMessage.success(`文件夹同步已${result.status === 'queued' ? '加入队列' : '完成'}`)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '同步失败'
    ElMessage.error(msg)
  } finally {
    syncingFolders.value = false
  }
}

// ---------- 测试连接 ----------

async function handleTest(id: number) {
  testingId.value = id
  try {
    const result = await testMailAccount(id)
    ElMessage.success(result.message || '连接测试通过')
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '连接测试失败'
    ElMessage.error(msg)
  } finally {
    testingId.value = null
  }
}

// ---------- 表单逻辑 ----------

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const defaultFormData: MailAccountRequest & { displayName: string } = {
  emailAddress: '',
  displayName: '',
  smtpHost: '',
  smtpPort: 465,
  smtpSsl: true,
  imapHost: '',
  imapPort: 993,
  imapSsl: true,
  authUsername: '',
  authPassword: '',
}

const formData = ref({ ...defaultFormData })

const formRules: FormRules = {
  emailAddress: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  smtpHost: [{ required: true, message: '请输入 SMTP 服务器地址', trigger: 'blur' }],
  smtpPort: [{ required: true, message: '请输入 SMTP 端口', trigger: 'blur' }],
  authUsername: [{ required: true, message: '请输入认证用户名', trigger: 'blur' }],
  authPassword: [{ required: true, message: '请输入密码', trigger: 'blur' }],
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

function openEditDialog(row: MailAccount) {
  isEditing.value = true
  editingId.value = row.id
  formData.value = {
    emailAddress: row.emailAddress,
    displayName: row.displayName || '',
    smtpHost: row.smtpHost,
    smtpPort: row.smtpPort,
    smtpSsl: row.smtpSsl,
    imapHost: row.imapHost || '',
    imapPort: row.imapPort ?? 993,
    imapSsl: row.imapSsl,
    authUsername: row.authUsername,
    authPassword: '', // 编辑时密码留空表示不修改
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  // 编辑模式下密码字段改为非必填验证
  if (isEditing.value && !formData.value.authPassword) {
    // 移除密码校验
  }

  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload: MailAccountRequest = {
      emailAddress: formData.value.emailAddress,
      displayName: formData.value.displayName || undefined,
      smtpHost: formData.value.smtpHost,
      smtpPort: formData.value.smtpPort,
      smtpSsl: formData.value.smtpSsl,
      imapHost: formData.value.imapHost || undefined,
      imapPort: formData.value.imapPort || undefined,
      imapSsl: formData.value.imapSsl,
      authUsername: formData.value.authUsername,
      authPassword: formData.value.authPassword,
    }

    if (isEditing.value && editingId.value !== null) {
      await updateMailAccount(editingId.value, payload)
      ElMessage.success('账号已更新')
    } else {
      await createMailAccount(payload)
      ElMessage.success('账号已创建')
    }
    dialogVisible.value = false
    await loadAccounts()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

// ---------- 手动接收邮件 ----------

const processDialogVisible = ref(false)
const processingMail = ref(false)
const processFormRef = ref<FormInstance>()

const defaultProcessForm: ProcessMailRequest & { userId: number } = {
  userId: 1,
  accountId: 0,
  messageUid: '',
  fromAddress: '',
  to: [],
  subject: '',
  content: '',
}

const processForm = ref({ ...defaultProcessForm })

const processFormRules: FormRules = {
  accountId: [{ required: true, message: '请选择发件账号', trigger: 'change' }],
  fromAddress: [
    { required: true, message: '请输入发件人地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  messageUid: [{ required: true, message: '请输入邮件UID', trigger: 'blur' }],
  subject: [{ required: true, message: '请输入邮件主题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入邮件正文', trigger: 'blur' }],
}

function resetProcessForm() {
  processForm.value = { ...defaultProcessForm }
  processFormRef.value?.resetFields()
}

function openProcessDialog() {
  resetProcessForm()
  // 默认选中第一个可用账号
  if (accounts.value.length > 0) {
    const active = accounts.value.find((a) => a.status === 1)
    processForm.value.accountId = active?.id ?? accounts.value[0].id
  }
  processDialogVisible.value = true
}

async function handleProcessMail() {
  const valid = await processFormRef.value?.validate().catch(() => false)
  if (!valid) return

  processingMail.value = true
  try {
    const result = await processMail({
      userId: processForm.value.userId,
      accountId: processForm.value.accountId,
      messageUid: processForm.value.messageUid,
      fromAddress: processForm.value.fromAddress,
      to: processForm.value.to.length > 0 ? processForm.value.to : [processForm.value.fromAddress],
      subject: processForm.value.subject,
      content: processForm.value.content,
    })
    ElMessage.success(
      `邮件已接收并分析完成：垃圾=${result.spamLabel} 优先级=${result.priorityLabel} 风险=${result.riskLevel}`,
    )
    processDialogVisible.value = false
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '接收邮件失败'
    ElMessage.error(msg)
  } finally {
    processingMail.value = false
  }
}

// ---------- 删除 ----------

async function handleDelete(row: MailAccount) {
  try {
    await ElMessageBox.confirm(
      `确认删除邮箱账号 "${row.emailAddress}"？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' },
    )
    await deleteMailAccount(row.id)
    ElMessage.success('已删除')
    await loadAccounts()
  } catch {
    // 用户取消
  }
}

// ---------- 工具函数 ----------

function formatDateTime(isoString: string | null): string {
  if (!isoString) return ''
  return new Date(isoString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ---------- 初始化 ----------

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.settings-page {
  max-width: 960px;
  margin: 0 auto;
}

.settings-section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-desc {
  margin: 0 0 16px;
  font-size: 13px;
  color: #9ca3af;
}

.account-table {
  margin-bottom: 20px;
}

.ssl-tag {
  margin-left: 6px;
}

.switch-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #9ca3af;
}

.text-muted {
  color: #9ca3af;
}
</style>
