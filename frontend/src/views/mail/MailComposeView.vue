<template>
  <div class="mail-compose">
    <el-button text @click="router.back()">返回</el-button>
    <el-empty description="写邮件功能开发中" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
