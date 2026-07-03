<template>
  <main class="mail-shell">
    <!-- 侧边栏 -->
    <aside class="mail-sidebar">
      <header class="sidebar-header">
        <h1>📧 邮件系统</h1>
        <el-button type="primary" size="small" class="compose-btn" @click="router.push('/compose')">
          <el-icon><Edit /></el-icon>
          写邮件
        </el-button>
      </header>

      <!-- 文件夹菜单 -->
      <nav class="folder-nav">
        <div
          v-for="folder in folderList"
          :key="folder.id"
          class="folder-item"
          :class="{ active: mailStore.currentFolderId === folder.id }"
          @click="selectFolder(folder)"
        >
          <el-icon class="folder-icon" :size="16">
            <component :is="folderIcon(folder.type)" />
          </el-icon>
          <span class="folder-name">{{ folderLabel(folder) }}</span>
          <el-badge
            v-if="folder.unreadCount > 0"
            :value="folder.unreadCount"
            :max="999"
            class="unread-badge"
          />
        </div>
      </nav>

      <el-divider />

      <!-- 底部菜单 -->
      <nav class="bottom-nav">
        <div
          class="folder-item"
          :class="{ active: route.path === '/contacts' }"
          @click="router.push('/contacts')"
        >
          <el-icon :size="16"><User /></el-icon>
          <span class="folder-name">通讯录</span>
        </div>
        <div
          class="folder-item"
          :class="{ active: route.path === '/settings' }"
          @click="router.push('/settings')"
        >
          <el-icon :size="16"><Setting /></el-icon>
          <span class="folder-name">设置</span>
        </div>
      </nav>

      <!-- 底部用户区 -->
      <div class="sidebar-footer">
        <div class="user-info" v-if="authStore.user">
          <el-avatar :size="28">{{ authStore.user.displayName?.charAt(0) }}</el-avatar>
          <span class="user-name">{{ authStore.user.displayName }}</span>
        </div>
        <el-button text size="small" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>
    </aside>

    <!-- 内容区 -->
    <section class="mail-content">
      <router-view />
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Edit, SwitchButton, User, Setting,
  Message, Promotion, Files, Delete, WarningFilled, Folder,
} from '@element-plus/icons-vue'
import type { FolderItem } from '@/types/folder'
import { getFolderList } from '@/api/folder'
import { logout } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { useMailStore } from '@/stores/mail'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const mailStore = useMailStore()

const folderList = ref<FolderItem[]>([])
const foldersLoading = ref(false)

// 文件夹图标映射
function folderIcon(type: FolderItem['type']) {
  const map: Record<string, typeof Message> = {
    inbox: Message,
    sent: Promotion,
    draft: Files,
    trash: Delete,
    spam: WarningFilled,
    custom: Folder,
  }
  return map[type] || Folder
}

// 文件夹显示名称
function folderLabel(folder: FolderItem): string {
  const typeLabels: Record<string, string> = {
    inbox: '收件箱',
    sent: '已发送',
    draft: '草稿箱',
    trash: '已删除',
    spam: '垃圾邮件',
  }
  return typeLabels[folder.type] || folder.name
}

// 选择文件夹 → 设置筛选 → 跳转邮件列表
function selectFolder(folder: FolderItem) {
  mailStore.setCurrentFolder(folder.id, folder.type)
  if (route.path !== '/') {
    router.push('/')
  }
}

// 加载文件夹列表
async function loadFolders() {
  foldersLoading.value = true
  try {
    folderList.value = await getFolderList()
    // 默认选中收件箱
    const inbox = folderList.value.find((f) => f.type === 'inbox')
    if (inbox && !mailStore.currentFolderId) {
      mailStore.setCurrentFolder(inbox.id, 'inbox')
    }
  } catch {
    // 静默处理，侧边栏回退到空状态
  } finally {
    foldersLoading.value = false
  }
}

// 退出登录
async function handleLogout() {
  try {
    await logout()
  } finally {
    authStore.clearSession()
    mailStore.resetMailList()
    router.push('/login')
  }
}

onMounted(() => {
  loadFolders()
  // 预加载邮箱账号列表（撰写邮件时需要）
  mailStore.fetchAccounts()
})
</script>

<style scoped>
.sidebar-header {
  margin-bottom: 16px;
}
.sidebar-header h1 {
  margin: 0 0 12px;
  font-size: 18px;
}
.compose-btn {
  width: 100%;
}

.folder-nav,
.bottom-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: #4b5563;
  font-size: 14px;
  transition: background 0.15s;
  user-select: none;
}
.folder-item:hover {
  background: #f3f4f6;
}
.folder-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}

.folder-icon {
  flex-shrink: 0;
  color: inherit;
}
.folder-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-badge {
  flex-shrink: 0;
}

.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name {
  font-size: 13px;
  color: #374151;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
