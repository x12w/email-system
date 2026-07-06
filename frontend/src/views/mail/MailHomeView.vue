<template>
  <main class="mail-shell">
    <!-- 顶栏：搜索 + 账号菜单 -->
    <header class="app-topbar">
      <div class="topbar-left">
        <h1 class="topbar-brand">邮件系统</h1>
      </div>
      <div class="topbar-center">
        <el-input
          v-model="filters.keyword"
          class="topbar-search"
          clearable
          placeholder="搜索邮件"
          :prefix-icon="Search"
          @keyup.enter="loadMessages"
          @clear="loadMessages"
        />
      </div>
      <div class="topbar-right">
        <el-badge :value="unreadPushCount" :hidden="unreadPushCount === 0">
          <el-button :icon="Bell" circle @click="showPushEvents = true" />
        </el-badge>

        <el-popover placement="bottom-end" width="320" trigger="click">
          <template #reference>
            <el-button class="account-menu-trigger">
              <span class="current-account">{{ activeAccount?.emailAddress || '未选择' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </el-button>
          </template>

          <!-- 账号管理菜单 -->
          <section class="account-menu">
            <header>当前邮箱</header>
            <div class="account-list">
              <div
                v-for="acc in accounts"
                :key="acc.id"
                class="menu-account-item"
                :class="{ active: acc.id === activeAccountId }"
              >
                <div class="menu-account-info" @click="switchAccount(acc.id)">
                  <strong>{{ acc.displayName || acc.emailAddress }}</strong>
                  <small>{{ acc.emailAddress }}</small>
                </div>
                <el-button :icon="Close" size="small" circle class="menu-account-remove"
                  @click.stop="removeAccount(acc.id, acc.emailAddress)" />
              </div>
            </div>

            <div class="menu-section">
              <el-button :icon="Plus" @click="openAccountDrawer">添加邮箱账号</el-button>
              <el-button :icon="Refresh" @click="loadAll">同步邮件</el-button>
            </div>
            <div class="menu-section">
              <el-button :icon="User" @click="showContacts = true">联系人</el-button>
              <el-button :icon="isDarkMode ? Sunny : Moon" @click="toggleTheme">
                {{ isDarkMode ? '浅色模式' : '暗黑模式' }}
              </el-button>
              <el-button :icon="SwitchButton" @click="logout">退出登录</el-button>
            </div>
          </section>
        </el-popover>
      </div>
    </header>

    <!-- 侧边栏：仅文件夹导航 -->
    <aside class="mail-sidebar">
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
    </aside>

    <!-- 主区域：列表 / 详情 单面板切换 -->
    <section class="mail-main">
      <!-- 邮件列表视图 -->
      <template v-if="!selectedMessage">
        <header class="workspace-header">
          <div>
            <span class="section-kicker">{{ activeAccount?.emailAddress || '未选择邮箱' }}</span>
            <h2>{{ selectedFolderName }}</h2>
          </div>
          <div class="summary-strip">
            <div><strong>{{ messages.length }}</strong><span>当前</span></div>
            <div><strong>{{ unreadCount }}</strong><span>未读</span></div>
            <div><strong>{{ highRiskCount }}</strong><span>风险</span></div>
          </div>
        </header>

        <header class="mail-toolbar">
          <el-radio-group v-model="filters.readState" @change="loadMessages" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="unread">未读</el-radio-button>
            <el-radio-button label="read">已读</el-radio-button>
          </el-radio-group>
          <el-select v-model="filters.priorityLabel" clearable placeholder="优先级" size="small" @change="loadMessages">
            <el-option label="高" value="high" />
            <el-option label="普通" value="normal" />
          </el-select>
          <el-select v-model="filters.riskLevel" clearable placeholder="风险" size="small" @change="loadMessages">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </header>

        <div class="active-filters">
          <el-tag v-if="filters.keyword" closable @close="clearFilter('keyword')">关键词：{{ filters.keyword }}</el-tag>
          <el-tag v-if="filters.priorityLabel" closable type="warning" @close="clearFilter('priorityLabel')">
            高优先
          </el-tag>
          <el-tag v-if="filters.riskLevel" closable type="danger" @close="clearFilter('riskLevel')">
            {{ riskLabel(filters.riskLevel) }}
          </el-tag>
        </div>

        <el-skeleton v-if="loading" :rows="8" animated />
        <div v-else class="message-list">
          <button
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="{ unread: !message.read }"
            @click="openMessage(message.id)"
          >
            <span class="read-dot" />
            <span class="message-sender">{{ message.fromName || message.fromAddress }}</span>
            <span class="message-subject">{{ message.subject }}</span>
            <span class="message-preview">{{ message.preview }}</span>
            <span class="message-badges">
              <el-tag v-if="message.priorityLabel === 'high'" size="small" type="warning">高优先</el-tag>
              <el-tag v-if="['medium','high','critical'].includes(message.riskLevel)" size="small" type="danger">
                {{ riskLabel(message.riskLevel) }}
              </el-tag>
              <el-tag v-if="message.spamLabel === 'spam'" size="small" type="info">垃圾</el-tag>
            </span>
            <span class="message-time">{{ formatTime(message.receivedAt) }}</span>
          </button>
          <el-empty v-if="messages.length === 0" description="没有符合条件的邮件" />
        </div>
      </template>

      <!-- 邮件详情视图 -->
      <template v-else>
        <header class="detail-header">
          <div>
            <el-button text :icon="ArrowLeft" @click="backToList">返回列表</el-button>
            <h2>{{ selectedMessage.subject }}</h2>
            <p>{{ selectedMessage.fromName }} &lt;{{ selectedMessage.fromAddress }}&gt;</p>
          </div>
          <div class="detail-actions">
            <el-tooltip :content="selectedMessage.read ? '标为未读' : '标为已读'">
              <el-button :icon="View" circle @click="toggleRead" />
            </el-tooltip>
            <el-tooltip content="删除">
              <el-button :icon="Delete" circle @click="removeSelectedMessage" />
            </el-tooltip>
            <el-button type="primary" :icon="Cpu" :loading="analyzing" @click="runAnalysis">智能分析</el-button>
          </div>
        </header>

        <div class="detail-meta">
          <span>收件人：{{ selectedMessage.to?.join(', ') }}</span>
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
          <div class="panel-title"><h3>智能分析</h3></div>
          <div v-if="analysis" class="analysis-grid">
            <div><span>垃圾分</span><el-progress :percentage="scorePercent(analysis.spamScore)" :stroke-width="8" /></div>
            <div><span>优先级分</span><el-progress :percentage="scorePercent(analysis.priorityScore)" :stroke-width="8" status="warning" /></div>
            <div><span>风险分</span><el-progress :percentage="scorePercent(analysis.riskScore)" :stroke-width="8" status="exception" /></div>
          </div>
          <el-table v-if="analysis?.threats.length" :data="analysis.threats" size="small">
            <el-table-column prop="type" label="类型" width="80" />
            <el-table-column prop="value" label="命中值" />
            <el-table-column prop="riskLevel" label="等级" width="80" />
            <el-table-column prop="reason" label="原因" />
          </el-table>
        </section>
      </template>
    </section>
  </main>

  <!-- 写邮件抽屉 -->
  <el-drawer v-model="composeVisible" title="写邮件" size="560px">
    <el-form label-position="top">
      <el-form-item label="账号">
        <el-select v-model="composeForm.accountId">
          <el-option v-for="acc in accounts" :key="acc.id" :label="acc.emailAddress" :value="acc.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="收件人">
        <el-input v-model="composeTo" placeholder="user@example.com" />
      </el-form-item>
      <el-form-item label="主题">
        <el-input v-model="composeForm.subject" />
      </el-form-item>
      <el-form-item label="正文">
        <el-input v-model="composeForm.content" type="textarea" :rows="12" />
      </el-form-item>
      <div class="drawer-actions">
        <el-button @click="saveAsDraft">存草稿</el-button>
        <el-button type="primary" @click="sendCurrentMessage">发送</el-button>
      </div>
    </el-form>
  </el-drawer>

  <!-- 添加账号抽屉 -->
  <el-drawer v-model="accountDrawerVisible" title="添加邮箱账号" size="480px">
    <el-form label-position="top">
      <el-form-item label="邮箱地址">
        <el-input v-model="accountForm.emailAddress" placeholder="admin@x12w.com" />
      </el-form-item>
      <el-form-item label="显示名称">
        <el-input v-model="accountForm.displayName" placeholder="Admin" />
      </el-form-item>
      <el-divider content-position="left">SMTP 发信</el-divider>
      <el-row :gutter="12">
        <el-col :span="16"><el-form-item label="服务器"><el-input v-model="accountForm.smtpHost" placeholder="smtp.resend.com" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="端口"><el-input-number v-model="accountForm.smtpPort" :min="1" /></el-form-item></el-col>
      </el-row>
      <el-checkbox v-model="accountForm.smtpSsl">SSL/TLS</el-checkbox>
      <el-divider content-position="left">IMAP 收信（可选）</el-divider>
      <el-row :gutter="12">
        <el-col :span="16"><el-form-item label="服务器"><el-input v-model="accountForm.imapHost" placeholder="imap.gmail.com" /></el-form-item></el-col>
        <el-col :span="8"><el-form-item label="端口"><el-input-number v-model="accountForm.imapPort" :min="1" /></el-form-item></el-col>
      </el-row>
      <el-checkbox v-model="accountForm.imapSsl">SSL/TLS</el-checkbox>
      <el-divider content-position="left">认证</el-divider>
      <el-form-item label="用户名"><el-input v-model="accountForm.authUsername" /></el-form-item>
      <el-form-item label="密码 / API Key"><el-input v-model="accountForm.authPassword" type="password" show-password /></el-form-item>
      <div class="drawer-actions">
        <el-button @click="accountDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingAccount" @click="addMailAccount">添加</el-button>
      </div>
    </el-form>
  </el-drawer>

  <!-- 联系人弹窗 -->
  <el-dialog v-model="showContacts" title="联系人" width="420px">
    <el-input v-model="contactKeyword" placeholder="搜索联系人" clearable @input="loadContacts" />
    <div class="contact-create">
      <el-input v-model="contactForm.name" placeholder="姓名" />
      <el-input v-model="contactForm.emailAddress" placeholder="邮箱" />
      <el-button type="primary" :icon="Plus" @click="addContact">新增</el-button>
    </div>
    <div class="contact-list">
      <p v-for="contact in contacts" :key="contact.id">{{ contact.name }} · {{ contact.emailAddress }}</p>
    </div>
  </el-dialog>

  <!-- 推送事件弹窗 -->
  <el-dialog v-model="showPushEvents" title="推送事件" width="420px">
    <div class="push-list">
      <button v-for="event in pushEvents" :key="event.id" @click="openPushEvent(event)">
        <strong>{{ event.title }}</strong><span>{{ event.content }}</span>
      </button>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import {
  ArrowDown, ArrowLeft, Bell, Close, Cpu, Delete, Document,
  EditPen, Fold, Folder, Message, Moon, Plus, Refresh,
  Search, Sunny, SwitchButton, User, View
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  analyzeMessage, createAccount, createContact, deleteAccount,
  deleteMessage, getIntelligenceResult, getMessage, listAccounts,
  listContacts, listFolders, listMessages, listPlugins,
  listPushEvents, markMessageRead, markPushEventRead, saveDraft,
  sendMessage, type Contact, type Folder as MailFolder,
  type IntelligenceResult, type MailAccount, type MailAccountRequest,
  type MessageDetail, type MessageSummary, type PluginStatus,
  type PushEvent, type SendMessageRequest
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
const showContacts = ref(false)
const showPushEvents = ref(false)
const composeTo = ref('')
const contactKeyword = ref('')

const filters = reactive({ keyword: '', priorityLabel: '', riskLevel: '', readState: 'all' })

const composeForm = reactive<SendMessageRequest>({
  accountId: 1, to: [], cc: [], bcc: [], subject: '',
  contentType: 'html', content: '', attachmentIds: []
})

const contactForm = reactive({ name: '', emailAddress: '', phone: '', remark: '' })

const accountForm = reactive({
  emailAddress: '', displayName: '', smtpHost: '', smtpPort: 587,
  smtpSsl: false, imapHost: '', imapPort: 993, imapSsl: true,
  authUsername: '', authPassword: ''
})

const activeAccount = computed(() => accounts.value.find(a => a.id === activeAccountId.value))
const visibleFolders = computed(() => folders.value.filter(f => f.accountId === activeAccountId.value))
const selectedFolderName = computed(() => visibleFolders.value.find(f => f.id === activeFolderId.value)?.name || '全部邮件')
const unreadCount = computed(() => messages.value.filter(m => !m.read).length)
const highRiskCount = computed(() => messages.value.filter(m => ['medium','high','critical'].includes(m.riskLevel)).length)
const unreadPushCount = computed(() => pushEvents.value.filter(e => !e.read).length)

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [accData, folderData, pluginData, pushData] = await Promise.all([
      listAccounts(), listFolders(), listPlugins(), listPushEvents()
    ])
    accounts.value = accData; folders.value = folderData
    plugins.value = pluginData; pushEvents.value = pushData
    if (!activeAccountId.value && accounts.value.length) activeAccountId.value = accounts.value[0].id
    composeForm.accountId = activeAccountId.value || 1
    if (!activeFolderId.value || !visibleFolders.value.some(f => f.id === activeFolderId.value)) {
      activeFolderId.value = visibleFolders.value[0]?.id
    }
    await loadMessages()
  } finally { loading.value = false }
}

async function loadMessages() {
  const result = await listMessages({
    folderId: activeFolderId.value,
    keyword: filters.keyword || undefined,
    read: filters.readState === 'all' ? undefined : filters.readState === 'read',
    priorityLabel: filters.priorityLabel || undefined,
    riskLevel: filters.riskLevel || undefined,
    page: 1, size: 50
  })
  messages.value = result.records
}

async function selectFolder(index: string) {
  activeFolderId.value = Number(index)
  selectedMessage.value = null; analysis.value = null
  await loadMessages()
}

async function switchAccount(id: number) {
  activeAccountId.value = id; composeForm.accountId = id
  activeFolderId.value = visibleFolders.value[0]?.id
  selectedMessage.value = null; analysis.value = null
  await loadMessages()
}

async function openMessage(id: number) {
  selectedMessage.value = await getMessage(id)
  analysis.value = await getIntelligenceResult(id)
}

function backToList() { selectedMessage.value = null; analysis.value = null }

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
    ElMessage.success('分析完成')
    await loadMessages()
  } finally { analyzing.value = false }
}

async function removeSelectedMessage() {
  if (!selectedMessage.value) return
  await deleteMessage(selectedMessage.value.id)
  selectedMessage.value = null; analysis.value = null
  ElMessage.success('已删除')
  await loadMessages()
}

function openCompose() { composeVisible.value = true }

function openAccountDrawer() {
  accountForm.emailAddress = ''; accountForm.displayName = ''
  accountForm.smtpHost = ''; accountForm.smtpPort = 587; accountForm.smtpSsl = false
  accountForm.imapHost = ''; accountForm.imapPort = 993; accountForm.imapSsl = true
  accountForm.authUsername = ''; accountForm.authPassword = ''
  accountDrawerVisible.value = true
}

async function addMailAccount() {
  if (!accountForm.emailAddress) { ElMessage.warning('请填写邮箱地址'); return }
  const hasSmtp = accountForm.smtpHost && accountForm.authUsername && accountForm.authPassword
  const hasImap = accountForm.imapHost && accountForm.authUsername && accountForm.authPassword
  if (!hasSmtp && !hasImap) { ElMessage.warning('请至少填写 SMTP 或 IMAP'); return }
  creatingAccount.value = true
  try {
    const req: MailAccountRequest = {
      emailAddress: accountForm.emailAddress.trim(),
      displayName: accountForm.displayName || accountForm.emailAddress,
      smtpHost: accountForm.smtpHost || '', smtpPort: accountForm.smtpPort || 587,
      smtpSsl: accountForm.smtpSsl, imapHost: accountForm.imapHost || '',
      imapPort: accountForm.imapPort || 993, imapSsl: accountForm.imapSsl,
      authUsername: accountForm.authUsername, authPassword: accountForm.authPassword
    }
    const acc = await createAccount(req)
    accountDrawerVisible.value = false; ElMessage.success('账号已添加')
    await loadAll(); await switchAccount(acc.id)
  } catch (e: any) { ElMessage.error(e?.message || '添加失败')
  } finally { creatingAccount.value = false }
}

async function removeAccount(id: number, email: string) {
  try {
    await ElMessageBox.confirm(`确定移除 "${email}"？`, '确认', { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' })
    await deleteAccount(id); ElMessage.success('已移除')
    if (activeAccountId.value === id) { activeAccountId.value = undefined; selectedMessage.value = null }
    await loadAll()
  } catch { /* cancelled */ }
}

async function sendCurrentMessage() {
  composeForm.to = splitRecipients(composeTo.value)
  await sendMessage(composeForm); resetCompose()
  ElMessage.success('已发送'); await loadMessages()
}

async function saveAsDraft() {
  composeForm.to = splitRecipients(composeTo.value)
  await saveDraft(composeForm); resetCompose()
  ElMessage.success('草稿已保存'); await loadMessages()
}

async function loadContacts() { contacts.value = await listContacts(contactKeyword.value) }

async function addContact() {
  if (!contactForm.name || !contactForm.emailAddress) { ElMessage.warning('请填写姓名和邮箱'); return }
  await createContact(contactForm)
  contactForm.name = ''; contactForm.emailAddress = ''; contactForm.phone = ''; contactForm.remark = ''
  await loadContacts(); ElMessage.success('已新增')
}

async function loadPushEvents() { pushEvents.value = await listPushEvents() }

async function openPushEvent(event: PushEvent) {
  await markPushEventRead(event.id); await loadPushEvents(); showPushEvents.value = false
  await openMessage(event.messageId)
}

async function logout() { authStore.clearSession(); await router.push('/login') }

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.dataset.theme = isDarkMode.value ? 'dark' : 'light'
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light')
}

function clearFilter(key: 'keyword' | 'priorityLabel' | 'riskLevel') { filters[key] = ''; loadMessages() }

function resetCompose() {
  composeVisible.value = false; composeTo.value = ''
  composeForm.subject = ''; composeForm.content = ''; composeForm.attachmentIds = []
}

function splitRecipients(value: string) { return value.split(',').map(s => s.trim()).filter(Boolean) }

function folderIcon(type: string) {
  if (type === 'draft') return Document; if (type === 'sent') return EditPen
  if (type === 'inbox') return Message; return Folder
}

function scorePercent(v: number) { return Math.round(Math.min(1, Math.max(0, v)) * 100) }
function riskTagType(v: string) { return ['medium','high','critical'].includes(v) ? 'danger' : 'success' }
function riskLabel(v: string) {
  const m: Record<string,string> = { none:'无风险', low:'低', medium:'中', high:'高', critical:'严重' }; return m[v] || v
}
function priorityLabel(v: string) { const m: Record<string,string> = { low:'低', normal:'普通', high:'高' }; return m[v] || v }
function formatTime(v: string) {
  return new Intl.DateTimeFormat('zh-CN', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit' }).format(new Date(v))
}
</script>
