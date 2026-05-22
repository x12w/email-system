<template>
  <main class="mail-shell">
    <aside class="mail-sidebar">
      <h1>邮件系统</h1>
      <el-menu :default-active="activeMenu" router @select="handleMenuSelect">
        <el-menu-item index="/">收件箱</el-menu-item>
        <el-menu-item index="/?folder=sent">已发送</el-menu-item>
        <el-menu-item index="/?folder=draft">草稿箱</el-menu-item>
        <el-menu-item index="/?folder=trash">已删除</el-menu-item>
        <el-menu-item index="/?folder=spam">垃圾邮件</el-menu-item>
        <el-divider />
        <el-menu-item index="/contacts">通讯录</el-menu-item>
        <el-menu-item index="/settings">设置</el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <el-button text @click="handleLogout">退出登录</el-button>
      </div>
    </aside>
    <section class="mail-content">
      <router-view />
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { logout } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/contacts')) return '/contacts'
  if (route.path.startsWith('/settings')) return '/settings'
  return '/'
})

async function handleLogout() {
  try {
    await logout()
  } finally {
    authStore.clearSession()
    router.push('/login')
  }
}

function handleMenuSelect(index: string) {
  router.push(index)
}
</script>

<style scoped>
.sidebar-footer {
  position: absolute;
  bottom: 16px;
  left: 12px;
  right: 12px;
}
</style>
