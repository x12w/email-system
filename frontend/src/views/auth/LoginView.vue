<template>
  <main class="auth-page">
    <section class="login-panel">
      <h1>邮件系统</h1>
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-alert v-if="errorMessage" class="login-error" :title="errorMessage" type="error" show-icon />
        <el-button type="primary" class="login-button" :loading="loading" @click="submit">登录</el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: 'admin',
  password: 'password'
})
const loading = ref(false)
const errorMessage = ref('')

async function submit() {
  loading.value = true
  errorMessage.value = ''
  try {
    const session = await login(form)
    authStore.setSession(session.accessToken, session.user)
    await router.push('/')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>
