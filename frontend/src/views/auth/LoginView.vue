<template>
  <main class="auth-page">
    <section class="login-panel">
      <h1>邮件系统</h1>
      <p class="login-subtitle">请使用管理员账号登录</p>

      <el-form
        ref="formRef"
        label-position="top"
        :model="form"
        :rules="rules"
        @submit.prevent="submit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            autocomplete="username"
            placeholder="请输入用户名"
            :prefix-icon="User"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
          >
            <template #suffix>
              <el-icon
                class="password-toggle"
                @click="showPassword = !showPassword"
              >
                <View v-if="!showPassword" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="submit"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <p v-if="errorMsg" class="error-msg">
        <el-icon><WarningFilled /></el-icon>
        {{ errorMsg }}
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Lock, View, Hide, WarningFilled } from '@element-plus/icons-vue'

import { login } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 4, message: '密码至少 4 位', trigger: 'blur' },
  ],
}

async function submit() {
  // 清除上次错误
  errorMsg.value = ''

  // 表单校验
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const session = await login(form)
    authStore.setSession(session.accessToken, session.refreshToken, session.user)
    await router.push('/')
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : '登录失败，请检查网络连接'
    errorMsg.value = message
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-panel {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.login-panel h1 {
  text-align: center;
  margin: 0 0 4px;
  font-size: 24px;
  color: #303133;
}

.login-subtitle {
  text-align: center;
  margin: 0 0 24px;
  color: #909399;
  font-size: 14px;
}

.login-button {
  width: 100%;
}

.password-toggle {
  cursor: pointer;
  color: #909399;
}
.password-toggle:hover {
  color: #409eff;
}

.error-msg {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 10px 12px;
  color: #f56c6c;
  font-size: 13px;
  background: #fef0f0;
  border-radius: 4px;
  border: 1px solid #fde2e2;
}
</style>
