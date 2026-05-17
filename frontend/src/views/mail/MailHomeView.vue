<template>
  <main class="mail-shell">
    <aside class="mail-sidebar">
      <h1>邮件系统</h1>
      <el-menu default-active="inbox">
        <el-menu-item index="inbox">收件箱</el-menu-item>
        <el-menu-item index="sent">已发送</el-menu-item>
        <el-menu-item index="draft">草稿箱</el-menu-item>
      </el-menu>
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

