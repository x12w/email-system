<template>
  <div class="mail-compose" v-loading="loadingDraft">
    <!-- 顶部操作栏 -->
    <header class="compose-header">
      <el-button text :icon="ArrowLeft" @click="handleBack">返回</el-button>
      <h2 class="compose-title">{{ isEditingDraft ? '编辑草稿' : '写邮件' }}</h2>
      <div class="compose-header-actions">
        <el-button :icon="Document" @click="handleSaveDraft" :loading="savingDraft">存草稿</el-button>
        <el-button type="primary" :icon="Promotion" @click="handleSend" :loading="mailStore.sending">
          发送
        </el-button>
      </div>
    </header>

    <!-- 错误提示 -->
    <el-alert
      v-if="errorMsg"
      :title="errorMsg"
      type="error"
      show-icon
      closable
      class="compose-alert"
      @close="errorMsg = ''"
    />

    <!-- 成功提示 -->
    <el-alert
      v-if="successMsg"
      :title="successMsg"
      type="success"
      show-icon
      closable
      class="compose-alert"
      @close="successMsg = ''"
    />

    <!-- 发件人选择 -->
    <div class="compose-field">
      <label class="compose-label">发件人</label>
      <el-select
        v-model="form.accountId"
        placeholder="选择发送账号"
        class="account-select"
        :loading="mailStore.accountsLoading"
        @focus="ensureAccounts"
      >
        <el-option
          v-for="acc in mailStore.accounts"
          :key="acc.id"
          :label="`${acc.displayName || ''} <${acc.emailAddress}>`"
          :value="acc.id"
        />
      </el-select>
    </div>

    <!-- 收件人（支持联系人自动补全） -->
    <div class="compose-field">
      <label class="compose-label">收件人</label>
      <el-select
        v-model="form.to"
        multiple
        filterable
        allow-create
        default-first-option
        placeholder="输入邮箱地址或选择联系人"
        class="recipient-select"
        :reserve-keyword="false"
        :loading="contactsLoading"
        @focus="ensureContacts"
        @remove-tag="onRemoveToTag"
      >
        <el-option
          v-for="contact in contactOptions"
          :key="contact.emailAddress"
          :label="`${contact.name} <${contact.emailAddress}>`"
          :value="contact.emailAddress"
        />
      </el-select>
    </div>

    <!-- 抄送（可折叠） -->
    <div class="compose-field">
      <label class="compose-label compose-label-clickable" @click="showCc = !showCc">
        <span>抄送</span>
        <el-icon :class="{ rotated: showCc }"><ArrowRight /></el-icon>
      </label>
      <el-select
        v-if="showCc"
        v-model="form.cc"
        multiple
        filterable
        allow-create
        default-first-option
        placeholder="输入邮箱地址或选择联系人"
        class="recipient-select"
        :reserve-keyword="false"
        :loading="contactsLoading"
      >
        <el-option
          v-for="contact in contactOptions"
          :key="'cc-' + contact.emailAddress"
          :label="`${contact.name} <${contact.emailAddress}>`"
          :value="contact.emailAddress"
        />
      </el-select>
    </div>

    <!-- 密送（可折叠） -->
    <div class="compose-field">
      <label class="compose-label compose-label-clickable" @click="showBcc = !showBcc">
        <span>密送</span>
        <el-icon :class="{ rotated: showBcc }"><ArrowRight /></el-icon>
      </label>
      <el-select
        v-if="showBcc"
        v-model="form.bcc"
        multiple
        filterable
        allow-create
        default-first-option
        placeholder="输入邮箱地址或选择联系人"
        class="recipient-select"
        :reserve-keyword="false"
        :loading="contactsLoading"
      >
        <el-option
          v-for="contact in contactOptions"
          :key="'bcc-' + contact.emailAddress"
          :label="`${contact.name} <${contact.emailAddress}>`"
          :value="contact.emailAddress"
        />
      </el-select>
    </div>

    <!-- 主题 -->
    <div class="compose-field">
      <label class="compose-label">主题</label>
      <el-input v-model="form.subject" placeholder="邮件主题" maxlength="200" show-word-limit />
    </div>

    <!-- 正文编辑器 -->
    <div class="compose-field compose-body-field">
      <label class="compose-label">
        正文
        <span class="content-type-toggle">
          <el-radio-group v-model="contentMode" size="small">
            <el-radio-button value="richtext">富文本</el-radio-button>
            <el-radio-button value="html">HTML</el-radio-button>
            <el-radio-button value="text">纯文本</el-radio-button>
          </el-radio-group>
        </span>
      </label>

      <!-- 富文本模式 -->
      <div v-if="contentMode === 'richtext'" class="richtext-editor">
        <div class="richtext-toolbar">
          <el-button-group size="small">
            <el-button @click="execCmd('bold')"><strong>B</strong></el-button>
            <el-button @click="execCmd('italic')"><em>I</em></el-button>
            <el-button @click="execCmd('underline')"><u>U</u></el-button>
            <el-button @click="execCmd('strikeThrough')"><s>S</s></el-button>
          </el-button-group>
          <el-button-group size="small" style="margin-left: 8px">
            <el-button :icon="List" @click="execCmd('insertUnorderedList')" />
            <el-button :icon="Tickets" @click="execCmd('insertOrderedList')" />
          </el-button-group>
          <el-button-group size="small" style="margin-left: 8px">
            <el-button @click="execCmd('formatBlock', '<p>')" size="small">段落</el-button>
            <el-button @click="execCmd('formatBlock', '<h3>')" size="small">标题</el-button>
          </el-button-group>
        </div>
        <div
          ref="editorRef"
          class="richtext-content"
          contenteditable
          @input="onEditorInput"
          @paste="onEditorPaste"
        />
      </div>

      <!-- HTML 源码模式 -->
      <el-input
        v-else-if="contentMode === 'html'"
        v-model="form.content"
        type="textarea"
        :rows="14"
        placeholder="输入 HTML 源码..."
        class="html-editor"
      />

      <!-- 纯文本模式 -->
      <el-input
        v-else
        v-model="form.content"
        type="textarea"
        :rows="14"
        placeholder="输入邮件正文..."
        class="text-editor"
      />
    </div>

    <!-- 附件区域 -->
    <div class="compose-field">
      <label class="compose-label">附件</label>
      <div class="attachment-area">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="onFileChange"
          accept="*"
          multiple
        >
          <el-button :icon="Paperclip" :loading="uploading">添加附件</el-button>
        </el-upload>

        <!-- 已添加的附件列表 -->
        <div v-if="attachments.length > 0" class="attachment-list">
          <div v-for="att in attachments" :key="att.tempId" class="attachment-item">
            <el-icon :size="18"><Document /></el-icon>
            <span class="att-name">{{ att.fileName }}</span>
            <span class="att-size">{{ formatSize(att.fileSize) }}</span>
            <span v-if="att.uploaded" class="att-uploaded">
              <el-icon color="#67c23a"><Check /></el-icon>
            </span>
            <span v-else-if="att.uploading" class="att-uploading">
              <el-icon class="is-loading"><Loading /></el-icon>
            </span>
            <el-button
              text
              size="small"
              type="danger"
              :icon="Close"
              :disabled="att.uploading"
              @click="removeAttachment(att.tempId)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile, UploadInstance } from 'element-plus'
import {
  ArrowLeft,
  ArrowRight,
  Document,
  Promotion,
  List,
  Tickets,
  Paperclip,
  Close,
  Check,
  Loading,
} from '@element-plus/icons-vue'
import { useMailStore } from '@/stores/mail'
import { getMailDetail, uploadAttachment } from '@/api/mail'
import { getContactList } from '@/api/contact'
import type { ContactItem } from '@/types/contact'

interface AttachmentEntry {
  tempId: number
  fileName: string
  fileSize: number
  uploaded: boolean
  uploading: boolean
  serverId: number | null
}

const route = useRoute()
const router = useRouter()
const mailStore = useMailStore()

// ---------- 表单数据 ----------

const form = reactive({
  accountId: null as number | null,
  to: [] as string[],
  cc: [] as string[],
  bcc: [] as string[],
  subject: '',
  content: '',
})

// ---------- UI 状态 ----------

const showCc = ref(false)
const showBcc = ref(false)
const contentMode = ref<'richtext' | 'html' | 'text'>('richtext')
const editorRef = ref<HTMLDivElement>()
const uploadRef = ref<UploadInstance>()
const attachments = ref<AttachmentEntry[]>([])
const uploading = ref(false)
const savingDraft = ref(false)
const loadingDraft = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
let tempIdCounter = 0

// 当前编辑的草稿 ID（从 query string 读取）
const draftId = ref<number | null>(null)
const isEditingDraft = ref(false)

// ---------- 联系人自动补全 ----------

const contacts = ref<ContactItem[]>([])
const contactsLoading = ref(false)
const contactOptions = ref<ContactItem[]>([])

async function ensureContacts() {
  if (contacts.value.length === 0) {
    contactsLoading.value = true
    try {
      contacts.value = await getContactList()
      contactOptions.value = contacts.value
    } catch {
      contacts.value = []
    } finally {
      contactsLoading.value = false
    }
  }
}

function onRemoveToTag() {
  // Element Plus select remove-tag 后不需要额外处理
}

// ---------- 账号加载 ----------

async function ensureAccounts() {
  if (mailStore.accounts.length === 0) {
    await mailStore.fetchAccounts()
  }
  // 默认选中第一个活跃账号（status === 1 表示活跃）
  if (!form.accountId && mailStore.accounts.length > 0) {
    const active = mailStore.accounts.find((a) => a.status === 1)
    form.accountId = active?.id ?? mailStore.accounts[0].id
  }
}

// ---------- 加载草稿 ----------

async function loadDraft(id: number) {
  loadingDraft.value = true
  try {
    const mail = await getMailDetail(id)
    if (!mail.draft) {
      errorMsg.value = '该邮件不是草稿，无法编辑'
      return
    }
    draftId.value = mail.id
    isEditingDraft.value = true
    form.accountId = mail.accountId
    form.subject = mail.subject || ''
    form.content = mail.content || ''

    // 填充收件人（后端返回 string[]，直接使用）
    if (mail.to && mail.to.length > 0) {
      form.to = mail.to
    }
    if (mail.cc && mail.cc.length > 0) {
      form.cc = mail.cc
      showCc.value = true
    }
    if (mail.bcc && mail.bcc.length > 0) {
      form.bcc = mail.bcc
      showBcc.value = true
    }

    // 恢复附件（已保存到服务端的附件）
    if (mail.attachments && mail.attachments.length > 0) {
      attachments.value = mail.attachments.map((a) => ({
        tempId: ++tempIdCounter,
        fileName: a.originalName,
        fileSize: a.sizeBytes,
        uploaded: true,
        uploading: false,
        serverId: a.id,
      }))
    }

    // 根据 contentType 设置编辑模式
    if (mail.contentType === 'html') {
      contentMode.value = 'richtext'
      // 富文本模式下将 HTML 加载到 contenteditable
      setTimeout(() => {
        if (editorRef.value) {
          editorRef.value.innerHTML = mail.content || ''
        }
      }, 0)
    } else {
      contentMode.value = 'text'
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '加载草稿失败'
    errorMsg.value = msg
  } finally {
    loadingDraft.value = false
  }
}

// ---------- 富文本操作 ----------

function execCmd(command: string, value?: string) {
  document.execCommand(command, false, value)
  editorRef.value?.focus()
  syncContentFromEditor()
}

function onEditorInput() {
  syncContentFromEditor()
}

function onEditorPaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/plain') || ''
  document.execCommand('insertText', false, text)
}

function syncContentFromEditor() {
  if (contentMode.value === 'richtext' && editorRef.value) {
    form.content = editorRef.value.innerHTML
  }
}

// 切换编辑模式时同步内容
watch(contentMode, (newMode, oldMode) => {
  if (oldMode === 'richtext' && editorRef.value) {
    form.content = editorRef.value.innerHTML
  }
  if (newMode === 'richtext') {
    setTimeout(() => {
      if (editorRef.value) {
        editorRef.value.innerHTML = form.content || ''
      }
    }, 0)
  }
})

// ---------- 附件处理 ----------

async function onFileChange(file: UploadFile) {
  if (!file.raw) return
  const entry: AttachmentEntry = {
    tempId: ++tempIdCounter,
    fileName: file.name,
    fileSize: file.size ?? 0,
    uploaded: false,
    uploading: true,
    serverId: null,
  }
  attachments.value.push(entry)

  try {
    const result = await uploadAttachment(file.raw)
    entry.serverId = result.id
    entry.uploaded = true
    entry.uploading = false
  } catch {
    ElMessage.error(`附件 "${file.name}" 上传失败`)
    attachments.value = attachments.value.filter((a) => a.tempId !== entry.tempId)
  }
}

async function removeAttachment(tempId: number) {
  attachments.value = attachments.value.filter((a) => a.tempId !== tempId)
}

// ---------- 获取当前有效的 attachmentIds ----------

function getAttachmentIds(): number[] {
  return attachments.value
    .filter((a) => a.uploaded && a.serverId !== null)
    .map((a) => a.serverId as number)
}

// ---------- 发送与保存 ----------

async function handleSend() {
  errorMsg.value = ''
  successMsg.value = ''

  // 表单验证
  if (!form.accountId) {
    errorMsg.value = '请选择发件账号'
    return
  }
  if (form.to.length === 0) {
    errorMsg.value = '请至少填写一个收件人'
    return
  }
  // 验证收件人邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  for (const email of form.to) {
    if (!emailRegex.test(email)) {
      errorMsg.value = `收件人邮箱格式不正确：${email}`
      return
    }
  }
  for (const email of form.cc) {
    if (!emailRegex.test(email)) {
      errorMsg.value = `抄送邮箱格式不正确：${email}`
      return
    }
  }
  for (const email of form.bcc) {
    if (!emailRegex.test(email)) {
      errorMsg.value = `密送邮箱格式不正确：${email}`
      return
    }
  }

  // 确保富文本内容已同步
  if (contentMode.value === 'richtext') {
    syncContentFromEditor()
  }

  const contentType: 'text' | 'html' = contentMode.value === 'text' ? 'text' : 'html'

  try {
    await mailStore.doSendMail({
      accountId: form.accountId,
      to: form.to,
      cc: form.cc.length > 0 ? form.cc : undefined,
      bcc: form.bcc.length > 0 ? form.bcc : undefined,
      subject: form.subject || '(无主题)',
      contentType,
      content: form.content || '',
      attachmentIds: getAttachmentIds().length > 0 ? getAttachmentIds() : undefined,
    })
    successMsg.value = '邮件发送成功'
    // 延迟返回列表，让用户看到成功提示
    setTimeout(() => {
      router.push('/')
    }, 1000)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '发送失败'
    errorMsg.value = msg
  }
}

async function handleSaveDraft() {
  errorMsg.value = ''
  successMsg.value = ''

  // 至少需要收件人或主题（否则完全空邮件）
  if (!form.accountId) {
    errorMsg.value = '请选择发件账号'
    return
  }

  if (contentMode.value === 'richtext') {
    syncContentFromEditor()
  }

  const contentType: 'text' | 'html' = contentMode.value === 'text' ? 'text' : 'html'
  savingDraft.value = true

  try {
    // B5 修复：空收件人时发送 [] 而不是 ['']
    const payload = {
      accountId: form.accountId,
      to: form.to.length > 0 ? form.to : [] as string[],
      cc: form.cc.length > 0 ? form.cc : undefined,
      bcc: form.bcc.length > 0 ? form.bcc : undefined,
      subject: form.subject || '',
      contentType,
      content: form.content || '',
      attachmentIds: getAttachmentIds().length > 0 ? getAttachmentIds() : undefined,
    }

    const savedId = await mailStore.doSaveDraft(payload)
    if (savedId && !draftId.value) {
      draftId.value = savedId
      isEditingDraft.value = true
    }
    successMsg.value = '草稿已保存'
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '保存草稿失败'
    errorMsg.value = msg
  } finally {
    savingDraft.value = false
  }
}

// ---------- 返回处理 ----------

async function handleBack() {
  // 如果表单有内容，提示是否放弃
  const hasContent = form.to.length > 0 || form.subject || form.content || attachments.value.length > 0
  if (hasContent) {
    try {
      await ElMessageBox.confirm('您有未保存的内容，确定要离开吗？', '提示', {
        confirmButtonText: '离开',
        cancelButtonText: '继续编辑',
        type: 'warning',
      })
    } catch {
      return
    }
  }
  router.back()
}

// ---------- 工具函数 ----------

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ---------- 初始化 ----------

onMounted(async () => {
  await ensureAccounts()

  // 检查是否编辑已有草稿
  const queryDraftId = route.query.draftId
  if (queryDraftId) {
    const id = Number(queryDraftId)
    if (!isNaN(id) && id > 0) {
      await loadDraft(id)
    }
  }
})
</script>

<style scoped>
.mail-compose {
  max-width: 860px;
  margin: 0 auto;
}

.compose-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.compose-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  color: #111827;
}

.compose-header-actions {
  display: flex;
  gap: 8px;
}

.compose-alert {
  margin-bottom: 16px;
}

.compose-field {
  display: flex;
  align-items: flex-start;
  margin-bottom: 14px;
}

.compose-label {
  min-width: 64px;
  padding-top: 6px;
  font-size: 14px;
  color: #374151;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.compose-label-clickable {
  cursor: pointer;
  user-select: none;
}
.compose-label-clickable:hover {
  color: #2563eb;
}

.compose-label .el-icon {
  transition: transform 0.2s;
}
.compose-label .el-icon.rotated {
  transform: rotate(90deg);
}

.account-select {
  width: 320px;
}

.recipient-select {
  flex: 1;
}

.content-type-toggle {
  margin-left: auto;
}

.compose-body-field {
  flex-direction: column;
}

.compose-body-field > .compose-label {
  margin-bottom: 8px;
  width: 100%;
}

/* 富文本编辑器 */
.richtext-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}

.richtext-toolbar {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
  flex-wrap: wrap;
  gap: 4px;
}

.richtext-content {
  min-height: 260px;
  padding: 12px 16px;
  outline: none;
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
  overflow-y: auto;
  max-height: 500px;
}

.richtext-content:empty::before {
  content: '请输入邮件正文...';
  color: #c0c4cc;
}

.richtext-content :deep(h3) {
  margin: 8px 0 4px;
  font-size: 16px;
}

.richtext-content :deep(p) {
  margin: 0 0 8px;
}

.richtext-content :deep(ul),
.richtext-content :deep(ol) {
  padding-left: 20px;
  margin: 0 0 8px;
}

.richtext-content :deep(blockquote) {
  margin: 8px 0;
  padding: 4px 12px;
  border-left: 3px solid #d1d5db;
  color: #6b7280;
}

.html-editor,
.text-editor {
  width: 100%;
}

/* 附件区域 */
.attachment-area {
  flex: 1;
}

.attachment-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
}

.attachment-item .att-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #374151;
}

.attachment-item .att-size {
  color: #9ca3af;
  font-size: 12px;
}

.att-uploaded {
  display: flex;
  align-items: center;
}

.att-uploading {
  display: flex;
  align-items: center;
}
</style>
