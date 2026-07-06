<template>
  <main class="mail-shell">
    <aside class="mail-sidebar">
      <header class="sidebar-header">
        <h1>邮件系统</h1>
        <span class="user-name">{{ authStore.user?.displayName }}</span>
      </header>
      <el-menu default-active="inbox">
        <el-menu-item index="inbox">收件箱</el-menu-item>
        <el-menu-item index="sent">已发送</el-menu-item>
        <el-menu-item index="draft">草稿箱</el-menu-item>
      </el-menu>
      <el-button class="logout-btn" @click="handleLogout">退出登录</el-button>
    </aside>
    <section class="mail-content">
      <header class="mail-toolbar">
        <el-button type="primary">写邮件</el-button>
        <el-input placeholder="搜索邮件" />
      </header>
      <el-empty description="等待接入邮件列表接口" />
    </section>
  </main>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
.logout-btn {
  margin: 12px;
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
