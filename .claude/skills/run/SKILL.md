---
name: run
description: 一键启动邮箱系统（后端 + 前端），进行前后端联调、展示、功能验证
color: green
---

# Run: 邮箱系统（前后端联调）

一键启动后端 Spring Boot（8080 端口）+ 前端 Vite（5173 端口）。

## 启动

```powershell
.claude\skills\run\driver.ps1
```

## 停止

```powershell
.claude\skills\run\driver.ps1 -Stop
```

## 访问

- 前台页面：http://localhost:5173
- 后端 API：http://localhost:8080/api
- 登录账号：admin / password

## 手动启动方式

打开两个终端：

**终端 1**（后端）：
```powershell
cd backend
mvn spring-boot:run
```

**终端 2**（前端）：
```powershell
cd frontend
pnpm dev
```
