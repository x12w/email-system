<template>
  <div>
    <header class="contacts-header">
      <h2>联系人</h2>
      <el-button type="primary" @click="showForm = true; editing = false">添加联系人</el-button>
    </header>

    <el-table v-if="contacts.length > 0" :data="contacts" style="width: 100%">
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="emailAddress" label="邮箱地址" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="remark" label="备注" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button size="small" @click="editContact(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无联系人" />

    <el-dialog v-model="showForm" :title="editing ? '编辑联系人' : '添加联系人'" width="500px">
      <el-form label-position="top">
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="邮箱地址">
          <el-input v-model="form.emailAddress" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listContacts, createContact, updateContact, deleteContact } from '@/api/mail'
import type { Contact } from '@/api/mail'

const contacts = ref<Contact[]>([])
const showForm = ref(false)
const editing = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const form = ref({
  name: '',
  emailAddress: '',
  phone: '',
  remark: ''
})

onMounted(loadContacts)

async function loadContacts() {
  contacts.value = await listContacts()
}

function editContact(c: Contact) {
  editing.value = true
  editingId.value = c.id
  form.value = { name: c.name, emailAddress: c.emailAddress, phone: c.phone || '', remark: c.remark || '' }
  showForm.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editing.value && editingId.value) {
      await updateContact(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createContact(form.value)
      ElMessage.success('添加成功')
    }
    showForm.value = false
    await loadContacts()
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定删除该联系人？')
    await deleteContact(id)
    ElMessage.success('删除成功')
    await loadContacts()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.contacts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.contacts-header h2 {
  margin: 0;
}
</style>
