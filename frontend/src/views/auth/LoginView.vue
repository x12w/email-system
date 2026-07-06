<template>
  <main class="auth-page">
    <section class="login-panel">
      <header class="login-header">
        <h1>邮件系统</h1>
      </header>

      <div class="auth-mode" role="tablist" aria-label="登录方式">
        <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册邮箱</button>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <label>
          <span>用户名</span>
          <input v-model="form.username" autocomplete="username" name="username" placeholder="请输入用户名" />
        </label>
        <label v-if="mode === 'register'">
          <span>显示名称</span>
          <input v-model="form.displayName" autocomplete="name" name="displayName" placeholder="例如：张三" />
        </label>
        <label v-if="mode === 'register'">
          <span>邮箱地址</span>
          <input v-model="form.emailAddress" autocomplete="email" name="email" placeholder="name@example.com" />
        </label>
        <label>
          <span>密码</span>
          <input
            v-model="form.password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            name="password"
            placeholder="请输入密码"
            type="password"
          />
        </label>
        <el-alert v-if="errorMessage" class="login-error" :title="errorMessage" type="error" show-icon />
        <button class="login-button" type="submit" :disabled="loading">
          {{ loading ? '处理中' : mode === 'login' ? '登录' : '注册邮箱并登录' }}
        </button>
      </form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { login, register } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: 'admin',
  password: 'password',
  displayName: '',
  emailAddress: ''
})
const loading = ref(false)
const errorMessage = ref('')
const mode = ref<'login' | 'register'>('login')

async function submit() {
  if (!form.username.trim() || !form.password) {
    errorMessage.value = '请输入用户名和密码'
    return
  }
  if (mode.value === 'register' && !form.emailAddress.trim()) {
    errorMessage.value = '请输入邮箱地址'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const session = mode.value === 'login'
      ? await login({ username: form.username, password: form.password })
      : await register({
        username: form.username,
        password: form.password,
        displayName: form.displayName || form.username,
        emailAddress: form.emailAddress
      })
    authStore.setSession(session.accessToken, session.user)
    await router.push('/')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '操作失败'
  } finally {
    loading.value = false
  }
}
</script>
