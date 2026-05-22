<template>
  <div class="mail-detail">
    <el-button text @click="router.back()">返回列表</el-button>
    <el-empty description="邮件详情加载中" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
