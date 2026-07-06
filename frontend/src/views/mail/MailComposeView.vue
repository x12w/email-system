<template>
  <main class="compose-shell">
    <header class="compose-header">
      <h2>写邮件</h2>
      <div class="header-actions">
        <el-button @click="router.back()">取消</el-button>
        <el-button type="primary" :loading="sending" @click="handleSend">发送</el-button>
      </div>
    </header>

    <el-form label-position="top" class="compose-form">
      <el-form-item label="发件账号">
        <el-select v-model="form.accountId" class="full-width" placeholder="选择发件账号">
          <el-option
            v-for="acct in accounts"
            :key="acct.id"
            :label="`${acct.emailAddress}${acct.displayName ? ' (' + acct.displayName + ')' : ''}`"
            :value="acct.id"
          />
        </el-select>
        <p v-if="accounts.length === 0" class="hint">
          请先在账号设置中添加邮箱账号
        </p>
      </el-form-item>

      <el-form-item label="收件人">
        <el-select
          v-model="form.to"
          multiple
          allow-create
          filterable
          default-first-option
          class="full-width"
          placeholder="输入收件人邮箱地址"
        />
      </el-form-item>

      <el-form-item label="抄送">
        <el-select
          v-model="form.cc"
          multiple
          allow-create
          filterable
          class="full-width"
          placeholder="抄送（可选）"
        />
      </el-form-item>

      <el-form-item label="主题">
        <el-input v-model="form.subject" placeholder="邮件主题" class="full-width" />
      </el-form-item>

      <el-form-item label="正文">
        <div class="editor-toolbar">
          <el-button size="small" @click="insertTag('p')">正文</el-button>
          <el-button size="small" @click="insertTag('b')">粗体</el-button>
          <el-button size="small" @click="insertTag('a')">链接</el-button>
        </div>
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="12"
          class="full-width compose-editor"
          placeholder="邮件正文（支持 HTML）"
        />
      </el-form-item>

      <el-form-item label="附件">
        <el-upload
          :auto-upload="false"
          :on-change="handleFileChange"
          :file-list="fileList"
        >
          <el-button size="small">选择文件</el-button>
        </el-upload>
      </el-form-item>
    </el-form>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listAccounts, sendMessage, uploadAttachment } from '@/api/mail'
import type { MailAccount } from '@/api/mail'

const router = useRouter()

const accounts = ref<MailAccount[]>([])
const sending = ref(false)
const fileList = ref<any[]>([])

const form = reactive({
  accountId: null as number | null,
  to: [] as string[],
  cc: [] as string[],
  bcc: [] as string[],
  subject: '',
  content: ''
})

onMounted(async () => {
  try {
    accounts.value = await listAccounts()
  } catch {
    // accounts will be empty array
  }
})

async function handleSend() {
  if (!form.accountId) {
    ElMessage.warning('请选择发件账号')
    return
  }
  if (form.to.length === 0) {
    ElMessage.warning('请填写收件人')
    return
  }
  if (!form.subject.trim()) {
    ElMessage.warning('请填写邮件主题')
    return
  }

  sending.value = true
  try {
    // Upload attachments first
    const attachmentIds: number[] = []
    for (const f of fileList.values()) {
      const raw = f.raw || f
      const result = await uploadAttachment(raw)
      attachmentIds.push(result.id)
    }

    await sendMessage({
      accountId: form.accountId,
      to: form.to,
      cc: form.cc.length > 0 ? form.cc : undefined,
      bcc: form.bcc.length > 0 ? form.bcc : undefined,
      subject: form.subject,
      contentType: 'html',
      content: form.content || '',
      attachmentIds: attachmentIds.length > 0 ? attachmentIds : undefined
    })

    ElMessage.success('发送成功')
    router.back()
  } catch (e: any) {
    ElMessage.error(e.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function handleFileChange(file: any) {
  fileList.value = [...fileList.value, file]
}

function insertTag(tag: string) {
  const tagMap: Record<string, string> = {
    p: '<p></p>',
    b: '<strong></strong>',
    a: '<a href=""></a>'
  }
  form.content += tagMap[tag] || ''
}
</script>

<style scoped>
.compose-shell {
  max-width: 800px;
  padding: 24px;
}
.compose-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.compose-header h2 {
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.compose-form {
  max-width: 100%;
}
.full-width {
  width: 100%;
}
.hint {
  color: #999;
  font-size: 12px;
  margin: 4px 0 0;
}
.editor-toolbar {
  margin-bottom: 8px;
  display: flex;
  gap: 4px;
}
.compose-editor :deep(textarea) {
  font-family: monospace;
}
</style>
