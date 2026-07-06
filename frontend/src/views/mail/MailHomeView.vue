<template>
  <main class="mail-shell">
    <header class="app-topbar">
      <div class="topbar-actions">
        <el-input
          v-model="filters.keyword"
          class="topbar-search"
          clearable
          placeholder="搜索邮件"
          :prefix-icon="Search"
          @keyup.enter="loadMessages"
          @clear="loadMessages"
        />
        <el-popover placement="bottom-end" width="300" trigger="click" popper-class="account-menu-popover">
          <template #reference>
            <el-button class="collapse-menu-button" :icon="Fold" circle aria-label="账号菜单" />
          </template>
          <section class="account-menu">
            <header>
              <span>当前邮箱</span>
              <strong>{{ activeAccount?.emailAddress || '未选择' }}</strong>
            </header>
            <div class="account-menu-list">
              <button
                v-for="account in accounts"
                :key="account.id"
                class="menu-account-item"
                :class="{ active: account.id === activeAccountId }"
                @click="switchAccount(account.id)"
              >
                <span>{{ account.displayName || account.emailAddress }}</span>
                <small>{{ account.emailAddress }}</small>
              </button>
            </div>
            <div class="account-menu-actions">
              <el-button :icon="Refresh" @click="loadAll">同步邮件</el-button>
              <el-button :icon="isDarkMode ? Sunny : Moon" @click="toggleTheme">
                {{ isDarkMode ? '切换浅色模式' : '切换暗黑模式' }}
              </el-button>
              <el-button :icon="Plus" @click="openAccountDrawer">添加邮箱账号</el-button>
              <el-button :icon="SwitchButton" @click="logout">退出并切换登录账号</el-button>
            </div>
          </section>
        </el-popover>
      </div>
    </header>

    <aside class="mail-sidebar">
      <div class="brand-row">
        <div>
          <h1>{{ activeAccount?.emailAddress || '邮箱' }}</h1>
          <span>{{ selectedFolderName }}</span>
        </div>
      </div>

      <el-button class="compose-entry" type="primary" :icon="EditPen" @click="openCompose">写邮件</el-button>

      <nav class="folder-nav">
        <button
          v-for="folder in visibleFolders"
          :key="folder.id"
          class="folder-item"
          :class="{ active: folder.id === activeFolderId }"
          @click="selectFolder(String(folder.id))"
        >
          <el-icon><component :is="folderIcon(folder.type)" /></el-icon>
          <span>{{ folder.name }}</span>
          <strong>{{ folder.totalCount }}</strong>
          <el-badge v-if="folder.unreadCount" :value="folder.unreadCount" />
        </button>
      </nav>

      <section class="sidebar-section">
        <h2>邮箱账号</h2>
        <button
          v-for="account in accounts"
          :key="account.id"
          class="account-row account-switcher"
          :class="{ active: account.id === activeAccountId }"
          @click="switchAccount(account.id)"
        >
          <span>{{ account.displayName || account.emailAddress }}</span>
          <small>{{ account.emailAddress }}</small>
        </button>
      </section>

      <section class="sidebar-section">
        <h2>智能插件</h2>
        <div v-for="plugin in plugins" :key="plugin.name" class="plugin-row">
          <span>{{ plugin.name }}</span>
          <el-tag size="small" :type="plugin.enabled ? 'success' : 'info'">{{ plugin.status }}</el-tag>
        </div>
      </section>
    </aside>

    <section class="mail-list-pane">
      <header class="workspace-header">
        <div>
          <span class="section-kicker">{{ activeAccount?.emailAddress || '未选择邮箱' }}</span>
          <h2>{{ selectedFolderName }}</h2>
        </div>
        <div class="summary-strip">
          <div>
            <strong>{{ messages.length }}</strong>
            <span>当前列表</span>
          </div>
          <div>
            <strong>{{ unreadCount }}</strong>
            <span>未读</span>
          </div>
          <div>
            <strong>{{ highRiskCount }}</strong>
            <span>风险</span>
          </div>
        </div>
      </header>

      <header class="mail-toolbar">
        <el-input
          v-model="filters.keyword"
          class="mail-toolbar-search"
          clearable
          placeholder="搜索发件人、主题或正文摘要"
          :prefix-icon="Search"
          @keyup.enter="loadMessages"
          @clear="loadMessages"
        />
        <el-radio-group v-model="filters.readState" @change="loadMessages">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
          <el-radio-button label="read">已读</el-radio-button>
        </el-radio-group>
        <el-select v-model="filters.priorityLabel" clearable placeholder="优先级" @change="loadMessages">
          <el-option label="高优先级" value="high" />
          <el-option label="普通" value="normal" />
          <el-option label="低优先级" value="low" />
        </el-select>
        <el-select v-model="filters.riskLevel" clearable placeholder="风险等级" @change="loadMessages">
          <el-option label="高风险" value="high" />
          <el-option label="中风险" value="medium" />
          <el-option label="低风险" value="low" />
          <el-option label="无风险" value="none" />
        </el-select>
        <el-tooltip content="刷新" placement="bottom">
          <el-button :icon="Refresh" circle @click="loadAll" />
        </el-tooltip>
      </header>

      <div class="active-filters">
        <el-tag v-if="filters.keyword" closable @close="clearFilter('keyword')">关键词：{{ filters.keyword }}</el-tag>
        <el-tag v-if="filters.priorityLabel" closable type="warning" @close="clearFilter('priorityLabel')">
          优先级：{{ priorityLabel(filters.priorityLabel) }}
        </el-tag>
        <el-tag v-if="filters.riskLevel" closable type="danger" @close="clearFilter('riskLevel')">
          风险：{{ riskLabel(filters.riskLevel) }}
        </el-tag>
      </div>

      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else class="message-list">
        <button
          v-for="message in messages"
          :key="message.id"
          class="message-row"
          :class="{ active: selectedMessage?.id === message.id, unread: !message.read }"
          @click="openMessage(message.id)"
        >
          <span class="read-dot" />
          <span class="message-sender">{{ message.fromName || message.fromAddress }}</span>
          <span class="message-subject">{{ message.subject }}</span>
          <span class="message-preview">{{ message.preview }}</span>
          <span class="message-badges">
            <el-tag v-if="message.priorityLabel === 'high'" size="small" type="warning">高优先</el-tag>
            <el-tag v-if="['medium', 'high', 'critical'].includes(message.riskLevel)" size="small" type="danger">
              {{ riskLabel(message.riskLevel) }}
            </el-tag>
            <el-tag v-if="message.spamLabel === 'spam'" size="small" type="info">垃圾</el-tag>
          </span>
          <span class="message-time">{{ formatTime(message.receivedAt) }}</span>
        </button>
        <el-empty v-if="messages.length === 0" description="没有符合条件的邮件" />
      </div>
    </section>

    <section class="mail-detail-pane">
      <template v-if="selectedMessage">
        <header class="detail-header">
          <div>
            <span class="section-kicker">邮件详情</span>
            <h2>{{ selectedMessage.subject }}</h2>
            <p>{{ selectedMessage.fromName }} &lt;{{ selectedMessage.fromAddress }}&gt;</p>
          </div>
          <div class="detail-actions">
            <el-tooltip :content="selectedMessage.read ? '标为未读' : '标为已读'" placement="bottom">
              <el-button :icon="View" circle @click="toggleRead" />
            </el-tooltip>
            <el-tooltip content="删除邮件" placement="bottom">
              <el-button :icon="Delete" circle @click="removeSelectedMessage" />
            </el-tooltip>
            <el-button type="primary" :icon="Cpu" :loading="analyzing" @click="runAnalysis">智能分析</el-button>
          </div>
        </header>

        <div class="detail-meta">
          <span>收件人：{{ selectedMessage.to.join(', ') }}</span>
          <span>{{ formatTime(selectedMessage.receivedAt) }}</span>
        </div>

        <div class="status-line">
          <el-tag :type="selectedMessage.read ? 'info' : 'success'">{{ selectedMessage.read ? '已读' : '未读' }}</el-tag>
          <el-tag :type="selectedMessage.priorityLabel === 'high' ? 'warning' : 'info'">
            {{ priorityLabel(selectedMessage.priorityLabel) }}
          </el-tag>
          <el-tag :type="riskTagType(selectedMessage.riskLevel)">{{ riskLabel(selectedMessage.riskLevel) }}</el-tag>
          <el-tag v-if="selectedMessage.draft" type="info">草稿</el-tag>
        </div>

        <article class="message-body" v-html="selectedMessage.content" />

        <section class="intelligence-panel">
          <div class="panel-title">
            <h3>智能分析</h3>
            <span v-if="analysis">{{ analysis.pluginName }} · v{{ analysis.pluginVersion }}</span>
          </div>
          <div v-if="analysis" class="analysis-grid">
            <div>
              <span>垃圾分</span>
              <el-progress :percentage="scorePercent(analysis.spamScore)" :stroke-width="8" />
            </div>
            <div>
              <span>优先级分</span>
              <el-progress :percentage="scorePercent(analysis.priorityScore)" :stroke-width="8" status="warning" />
            </div>
            <div>
              <span>风险分</span>
              <el-progress :percentage="scorePercent(analysis.riskScore)" :stroke-width="8" status="exception" />
            </div>
          </div>
          <el-table v-if="analysis?.threats.length" :data="analysis.threats" size="small">
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column prop="value" label="命中值" />
            <el-table-column prop="riskLevel" label="等级" width="90" />
            <el-table-column prop="reason" label="原因" />
          </el-table>
          <el-empty v-else description="暂无风险命中" />
        </section>
      </template>

      <div v-else class="detail-empty">
        <el-icon><Message /></el-icon>
        <h2>请选择一封邮件</h2>
      </div>
    </section>
  </main>

  <el-drawer v-model="composeVisible" title="写邮件" size="560px">
    <el-form label-position="top">
      <el-form-item label="账号">
        <el-select v-model="composeForm.accountId">
          <el-option v-for="account in accounts" :key="account.id" :label="account.emailAddress" :value="account.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="收件人">
        <el-input v-model="composeTo" placeholder="user@example.com, team@example.com" />
      </el-form-item>
      <el-form-item label="主题">
        <el-input v-model="composeForm.subject" />
      </el-form-item>
      <el-form-item label="正文">
        <el-input v-model="composeForm.content" type="textarea" :rows="10" />
      </el-form-item>
      <div class="drawer-actions">
        <el-button @click="saveAsDraft">存草稿</el-button>
        <el-button type="primary" @click="sendCurrentMessage">发送</el-button>
      </div>
    </el-form>
  </el-drawer>

  <el-drawer v-model="accountDrawerVisible" title="添加邮箱账号" size="480px">
    <el-form label-position="top">
      <el-form-item label="邮箱地址" required>
        <el-input v-model="accountForm.emailAddress" placeholder="admin@mail.x12w.com" />
      </el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="accountForm.displayName" placeholder="Admin" />
      </el-form-item>
      <el-divider content-position="left">SMTP 发送服务器</el-divider>
      <el-row :gutter="12">
        <el-col :span="16">
          <el-form-item label="SMTP 服务器">
            <el-input v-model="accountForm.smtpHost" placeholder="smtp.resend.com" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="端口">
            <el-input-number v-model="accountForm.smtpPort" :min="1" :max="65535" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="">
        <el-checkbox v-model="accountForm.smtpSsl">启用 SSL/TLS（端口 465 时开启）</el-checkbox>
      </el-form-item>
      <el-divider content-position="left">IMAP 接收服务器（可选）</el-divider>
      <el-row :gutter="12">
        <el-col :span="16">
          <el-form-item label="IMAP 服务器">
            <el-input v-model="accountForm.imapHost" placeholder="imap.gmail.com" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="端口">
            <el-input-number v-model="accountForm.imapPort" :min="1" :max="65535" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="">
        <el-checkbox v-model="accountForm.imapSsl">启用 SSL/TLS</el-checkbox>
      </el-form-item>
      <el-divider content-position="left">认证信息</el-divider>
      <el-form-item label="认证用户名">
        <el-input v-model="accountForm.authUsername" placeholder="resend" />
      </el-form-item>
      <el-form-item label="认证密码 / API Key">
        <el-input v-model="accountForm.authPassword" type="password" show-password placeholder="re_xxx..." />
      </el-form-item>
      <div class="drawer-actions">
        <el-button @click="accountDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingAccount" @click="addMailAccount">添加账号</el-button>
      </div>
    </el-form>
  </el-drawer>

  <aside class="utility-rail">
    <el-popover placement="left" width="380" trigger="click" @show="loadContacts">
      <template #reference>
        <el-button :icon="User" circle />
      </template>
      <h3>联系人</h3>
      <el-input v-model="contactKeyword" placeholder="搜索联系人" clearable @input="loadContacts" />
      <div class="contact-create">
        <el-input v-model="contactForm.name" placeholder="姓名" />
        <el-input v-model="contactForm.emailAddress" placeholder="邮箱地址" />
        <el-button type="primary" :icon="Plus" @click="addContact">新增</el-button>
      </div>
      <div class="contact-list">
        <p v-for="contact in contacts" :key="contact.id">{{ contact.name }} · {{ contact.emailAddress }}</p>
      </div>
    </el-popover>
    <el-popover placement="left" width="400" trigger="click" @show="loadPushEvents">
      <template #reference>
        <el-badge :value="unreadPushCount" :hidden="unreadPushCount === 0">
          <el-button :icon="Bell" circle />
        </el-badge>
      </template>
      <h3>推送事件</h3>
      <div class="push-list">
        <button v-for="event in pushEvents" :key="event.id" @click="openPushEvent(event)">
          <strong>{{ event.title }}</strong>
          <span>{{ event.content }}</span>
        </button>
      </div>
    </el-popover>
  </aside>
</template>

<script setup lang="ts">
import {
  Bell,
  Cpu,
  Delete,
  Document,
  EditPen,
  Fold,
  Folder,
  Message,
  Moon,
  Plus,
  Refresh,
  Search,
  Sunny,
  SwitchButton,
  User,
  View
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  analyzeMessage,
  createAccount,
  createContact,
  deleteMessage,
  getIntelligenceResult,
  getMessage,
  listAccounts,
  listContacts,
  listFolders,
  listMessages,
  listPlugins,
  listPushEvents,
  markMessageRead,
  markPushEventRead,
  saveDraft,
  sendMessage,
  type Contact,
  type Folder as MailFolder,
  type IntelligenceResult,
  type MailAccount,
  type MailAccountRequest,
  type MessageDetail,
  type MessageSummary,
  type PluginStatus,
  type PushEvent,
  type SendMessageRequest
} from '@/api/mail'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const accounts = ref<MailAccount[]>([])
const folders = ref<MailFolder[]>([])
const messages = ref<MessageSummary[]>([])
const selectedMessage = ref<MessageDetail | null>(null)
const analysis = ref<IntelligenceResult | null>(null)
const contacts = ref<Contact[]>([])
const pushEvents = ref<PushEvent[]>([])
const plugins = ref<PluginStatus[]>([])
const activeFolderId = ref<number>()
const activeAccountId = ref<number>()
const loading = ref(false)
const analyzing = ref(false)
const isDarkMode = ref(document.documentElement.dataset.theme === 'dark')
const composeVisible = ref(false)
const accountDrawerVisible = ref(false)
const creatingAccount = ref(false)
const composeTo = ref('')
const contactKeyword = ref('')

const filters = reactive({
  keyword: '',
  priorityLabel: '',
  riskLevel: '',
  readState: 'all'
})

const composeForm = reactive<SendMessageRequest>({
  accountId: 1,
  to: [],
  cc: [],
  bcc: [],
  subject: '',
  contentType: 'html',
  content: '',
  attachmentIds: []
})

const contactForm = reactive({
  name: '',
  emailAddress: '',
  phone: '',
  remark: ''
})

const accountForm = reactive({
  emailAddress: '',
  displayName: '',
  smtpHost: '',
  smtpPort: 587,
  smtpSsl: false,
  imapHost: '',
  imapPort: 993,
  imapSsl: true,
  authUsername: '',
  authPassword: ''
})

const activeAccount = computed(() => accounts.value.find((account) => account.id === activeAccountId.value))
const visibleFolders = computed(() => folders.value.filter((folder) => folder.accountId === activeAccountId.value))
const selectedFolderName = computed(() => visibleFolders.value.find((folder) => folder.id === activeFolderId.value)?.name || '全部邮件')
const unreadCount = computed(() => messages.value.filter((message) => !message.read).length)
const highRiskCount = computed(() => messages.value.filter((message) => ['medium', 'high', 'critical'].includes(message.riskLevel)).length)
const unreadPushCount = computed(() => pushEvents.value.filter((event) => !event.read).length)

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [accountData, folderData, pluginData, pushData] = await Promise.all([
      listAccounts(),
      listFolders(),
      listPlugins(),
      listPushEvents()
    ])
    accounts.value = accountData
    folders.value = folderData
    plugins.value = pluginData
    pushEvents.value = pushData
    activeAccountId.value = activeAccountId.value || accounts.value[0]?.id
    composeForm.accountId = activeAccountId.value || accounts.value[0]?.id || 1
    if (!activeFolderId.value || !visibleFolders.value.some((folder) => folder.id === activeFolderId.value)) {
      activeFolderId.value = visibleFolders.value[0]?.id
    }
    await loadMessages()
    if (!selectedMessage.value && messages.value[0]) {
      await openMessage(messages.value[0].id)
    }
  } finally {
    loading.value = false
  }
}

async function loadMessages() {
  const result = await listMessages({
    folderId: activeFolderId.value,
    keyword: filters.keyword || undefined,
    read: filters.readState === 'all' ? undefined : filters.readState === 'read',
    priorityLabel: filters.priorityLabel || undefined,
    riskLevel: filters.riskLevel || undefined,
    page: 1,
    size: 50
  })
  messages.value = result.records
}

async function selectFolder(index: string) {
  activeFolderId.value = Number(index)
  selectedMessage.value = null
  analysis.value = null
  await loadMessages()
}

async function switchAccount(accountId: number) {
  activeAccountId.value = accountId
  composeForm.accountId = accountId
  activeFolderId.value = visibleFolders.value[0]?.id
  selectedMessage.value = null
  analysis.value = null
  await loadMessages()
}

async function openMessage(id: number) {
  selectedMessage.value = await getMessage(id)
  analysis.value = await getIntelligenceResult(id)
}

async function toggleRead() {
  if (!selectedMessage.value) return
  selectedMessage.value = await markMessageRead(selectedMessage.value.id, !selectedMessage.value.read)
  await loadMessages()
}

async function runAnalysis() {
  if (!selectedMessage.value) return
  analyzing.value = true
  try {
    analysis.value = await analyzeMessage(selectedMessage.value.id)
    selectedMessage.value = await getMessage(selectedMessage.value.id)
    ElMessage.success('智能分析已完成')
    await loadMessages()
  } finally {
    analyzing.value = false
  }
}

async function removeSelectedMessage() {
  if (!selectedMessage.value) return
  await deleteMessage(selectedMessage.value.id)
  selectedMessage.value = null
  analysis.value = null
  ElMessage.success('邮件已删除')
  await loadMessages()
}

function openCompose() {
  composeVisible.value = true
}

function openAccountDrawer() {
  accountForm.emailAddress = ''
  accountForm.displayName = ''
  accountForm.smtpHost = ''
  accountForm.smtpPort = 587
  accountForm.smtpSsl = false
  accountForm.imapHost = ''
  accountForm.imapPort = 993
  accountForm.imapSsl = true
  accountForm.authUsername = ''
  accountForm.authPassword = ''
  accountDrawerVisible.value = true
}

async function addMailAccount() {
  if (!accountForm.emailAddress) {
    ElMessage.warning('请填写邮箱地址')
    return
  }
  const hasSmtp = accountForm.smtpHost && accountForm.authUsername && accountForm.authPassword
  const hasImap = accountForm.imapHost && accountForm.authUsername && accountForm.authPassword
  if (!hasSmtp && !hasImap) {
    ElMessage.warning('请至少填写 SMTP 或 IMAP 服务器和认证信息')
    return
  }
  creatingAccount.value = true
  try {
    const emailAddress = accountForm.emailAddress.trim()
    const accountRequest: MailAccountRequest = {
      emailAddress,
      displayName: accountForm.displayName || emailAddress,
      smtpHost: accountForm.smtpHost || '',
      smtpPort: accountForm.smtpPort || 587,
      smtpSsl: accountForm.smtpSsl,
      imapHost: accountForm.imapHost || '',
      imapPort: accountForm.imapPort || 993,
      imapSsl: accountForm.imapSsl,
      authUsername: accountForm.authUsername,
      authPassword: accountForm.authPassword
    }
    const account = await createAccount(accountRequest)
    accountDrawerVisible.value = false
    ElMessage.success('邮箱账号已添加')
    await loadAll()
    await switchAccount(account.id)
  } catch (e: any) {
    ElMessage.error(e?.message || '添加失败')
  } finally {
    creatingAccount.value = false
  }
}

async function sendCurrentMessage() {
  composeForm.to = splitRecipients(composeTo.value)
  await sendMessage(composeForm)
  resetCompose()
  ElMessage.success('邮件已发送')
  await loadMessages()
}

async function saveAsDraft() {
  composeForm.to = splitRecipients(composeTo.value)
  await saveDraft(composeForm)
  resetCompose()
  ElMessage.success('草稿已保存')
  await loadMessages()
}

async function loadContacts() {
  contacts.value = await listContacts(contactKeyword.value)
}

async function addContact() {
  if (!contactForm.name || !contactForm.emailAddress) {
    ElMessage.warning('请填写姓名和邮箱地址')
    return
  }
  await createContact(contactForm)
  contactForm.name = ''
  contactForm.emailAddress = ''
  contactForm.phone = ''
  contactForm.remark = ''
  await loadContacts()
  ElMessage.success('联系人已新增')
}

async function loadPushEvents() {
  pushEvents.value = await listPushEvents()
}

async function openPushEvent(event: PushEvent) {
  await markPushEventRead(event.id)
  await loadPushEvents()
  await openMessage(event.messageId)
}

async function logout() {
  authStore.clearSession()
  await router.push('/login')
}

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value
  const theme = isDarkMode.value ? 'dark' : 'light'
  document.documentElement.dataset.theme = theme
  localStorage.setItem('theme', theme)
}

function clearFilter(key: 'keyword' | 'priorityLabel' | 'riskLevel') {
  filters[key] = ''
  void loadMessages()
}

function resetCompose() {
  composeVisible.value = false
  composeTo.value = ''
  composeForm.subject = ''
  composeForm.content = ''
  composeForm.attachmentIds = []
}

function splitRecipients(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function folderIcon(type: string) {
  if (type === 'draft') return Document
  if (type === 'sent') return EditPen
  if (type === 'inbox') return Message
  return Folder
}

function scorePercent(value: number) {
  return Math.round(Math.min(1, Math.max(0, value)) * 100)
}

function riskTagType(value: string) {
  return ['medium', 'high', 'critical'].includes(value) ? 'danger' : 'success'
}

function riskLabel(value: string) {
  const labels: Record<string, string> = {
    none: '无风险',
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    critical: '严重风险'
  }
  return labels[value] || value
}

function priorityLabel(value: string) {
  const labels: Record<string, string> = {
    low: '低优先',
    normal: '普通',
    high: '高优先'
  }
  return labels[value] || value
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(value))
}
</script>
