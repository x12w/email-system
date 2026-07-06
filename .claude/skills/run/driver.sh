#!/usr/bin/env bash
# Run the email system: backend + frontend
set -e

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "=== 启动后端 ==="
cd "$ROOT_DIR/backend"
mvn spring-boot:run > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
echo "等待后端启动..."
until grep -q "Started EmailSystemApplication" /tmp/backend.log 2>/dev/null; do
  sleep 2
done
echo "后端启动成功 (localhost:8080)"

echo "=== 启动前端 ==="
cd "$ROOT_DIR/frontend"
pnpm dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

sleep 3
echo "前端启动成功 (http://localhost:5173)"
echo ""
echo "访问 http://localhost:5173 查看"
echo "登录账号: admin / password"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
