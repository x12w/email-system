<template>
  <main class="mail-shell">
    <aside class="mail-sidebar">
      <header class="sidebar-header">
        <h1>邮件系统</h1>
        <span class="user-name">{{ authStore.user?.displayName }}</span>
      </header>
      <el-menu :default-active="route.path" @select="handleMenuSelect">
        <el-menu-item index="/inbox">收件箱</el-menu-item>
        <el-menu-item index="/sent">已发送</el-menu-item>
        <el-menu-item index="/draft">草稿箱</el-menu-item>
        <el-menu-item index="/contacts">联系人</el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <el-button class="sidebar-btn" @click="showAccounts = true">账号管理</el-button>
        <el-button class="logout-btn" @click="handleLogout">退出登录</el-button>
      </div>
    </aside>
    <section class="mail-content">
      <header class="mail-toolbar">
        <el-button type="primary" @click="router.push('/compose')">写邮件</el-button>
        <el-input placeholder="搜索邮件" />
      </header>

      <router-view />

      <el-empty v-if="noChildRoute" description="等待接入邮件列表接口" />
    </section>

    <!-- Account Management Dialog -->
    <el-dialog v-model="showAccounts" title="邮箱账号管理" width="700px">
      <template v-if="accounts.length === 0">
        <el-empty description="暂无邮箱账号" />
      </template>
      <el-table v-else :data="accounts" style="width: 100%">
        <el-table-column prop="emailAddress" label="邮箱地址" />
        <el-table-column prop="displayName" label="显示名称" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="testAccount(row.id)">测试</el-button>
            <el-button size="small" type="danger" @click="handleDeleteAccount(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="showAccounts = false">关闭</el-button>
        <el-button type="primary" @click="showAddForm = true">添加账号</el-button>
      </template>
    </el-dialog>

    <!-- Add Account Dialog -->
    <el-dialog v-model="showAddForm" title="添加邮箱账号" width="600px">
      <el-form label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="邮箱地址">
              <el-input v-model="addForm.emailAddress" placeholder="user@example.com" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示名称">
              <el-input v-model="addForm.displayName" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="SMTP 服务器">
              <el-input v-model="addForm.smtpHost" placeholder="smtp.example.com" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="SMTP 端口">
              <el-input-number v-model="addForm.smtpPort" :min="1" :max="65535" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="SSL">
              <el-switch v-model="addForm.smtpSsl" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="IMAP 服务器">
              <el-input v-model="addForm.imapHost" placeholder="imap.example.com" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="IMAP 端口">
              <el-input-number v-model="addForm.imapPort" :min="1" :max="65535" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="SSL">
              <el-switch v-model="addForm.imapSsl" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="认证用户名">
              <el-input v-model="addForm.authUsername" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证密码">
              <el-input v-model="addForm.authPassword" type="password" show-password />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showAddForm = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="handleAddAccount">保存</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listAccounts,
  createAccount,
  deleteAccount,
  testAccount as testAccountApi
} from '@/api/mail'
import type { MailAccount } from '@/api/mail'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const noChildRoute = computed(() => route.matched.length <= 1)

const currentFolder = ref('inbox')
const showAccounts = ref(false)
const showAddForm = ref(false)
const accounts = ref<MailAccount[]>([])
const adding = ref(false)

const addForm = ref({
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

async function loadAccounts() {
  try {
    accounts.value = await listAccounts()
  } catch {
    accounts.value = []
  }
}

onMounted(loadAccounts)

function handleMenuSelect(index: string) {
  // Contacts has its own route
  if (index === '/contacts') {
    router.push('/contacts')
    return
  }
  // Keep current page but set folder filter
  currentFolder.value = index.replace('/', '')
}

async function handleAddAccount() {
  adding.value = true
  try {
    await createAccount({
      emailAddress: addForm.value.emailAddress,
      displayName: addForm.value.displayName || undefined,
      smtpHost: addForm.value.smtpHost,
      smtpPort: addForm.value.smtpPort,
      smtpSsl: addForm.value.smtpSsl ? 1 : 0,
      imapHost: addForm.value.imapHost,
      imapPort: addForm.value.imapPort,
      imapSsl: addForm.value.imapSsl ? 1 : 0,
      authUsername: addForm.value.authUsername,
      authPassword: addForm.value.authPassword
    })
    ElMessage.success('添加成功')
    showAddForm.value = false
    await loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message || '添加失败')
  } finally {
    adding.value = false
  }
}

async function handleDeleteAccount(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该邮箱账号？')
    await deleteAccount(id)
    ElMessage.success('删除成功')
    await loadAccounts()
  } catch {
    // cancelled or failed
  }
}

async function testAccount(id: number) {
  try {
    await testAccountApi(id)
    ElMessage.success('连接测试通过')
  } catch (e: any) {
    ElMessage.error(e.message || '连接测试失败')
  }
}

function handleLogout() {
  authStore.clearSession()
  router.push('/login')
}
</script>

<style scoped>
.mail-shell {
  display: flex;
  height: 100vh;
}
.mail-sidebar {
  width: 240px;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}
.sidebar-header h1 {
  margin: 0 0 4px 0;
  font-size: 18px;
}
.user-name {
  font-size: 13px;
  color: #666;
}
.mail-sidebar .el-menu {
  flex: 1;
  border-right: none;
}
.sidebar-footer {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid #e0e0e0;
}
.sidebar-btn {
  width: 100%;
}
.logout-btn {
  width: 100%;
}
.mail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.mail-toolbar {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
}
.mail-toolbar .el-input {
  max-width: 320px;
}
</style>
