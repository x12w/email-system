#!/usr/bin/env pwsh
# 一键启动邮箱系统（后端 + 前端）
param([switch]$Stop)

$ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))

if ($Stop) {
  Write-Host "正在停止服务..."
  Get-Process -Name "java" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "email-system" } | Stop-Process -Force
  Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force
  Write-Host "已停止"
  return
}

Write-Host "=== 启动后端 ===" -ForegroundColor Green
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd '$ROOT\backend'; mvn spring-boot:run"

Write-Host "等待后端启动（约 30 秒）..." -ForegroundColor Yellow
Start-Sleep -Seconds 25

Write-Host "=== 启动前端 ===" -ForegroundColor Green
Start-Process powershell -WindowStyle Hidden -ArgumentList "-NoExit", "-Command", "cd '$ROOT\frontend'; pnpm dev"

Start-Sleep -Seconds 5
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ 启动完成！" -ForegroundColor Green
Write-Host "  前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "  登录: admin / password" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "关闭服务请运行: .\.claude\skills\run\driver.ps1 -Stop" -ForegroundColor Yellow
