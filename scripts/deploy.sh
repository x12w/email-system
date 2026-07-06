#!/usr/bin/env bash
set -euo pipefail

# ============================================
# Email System — 一键部署与管理脚本
# ============================================

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
ENV_FILE="$PROJECT_DIR/.env"
BACKEND_LOG="$PROJECT_DIR/data/backend.log"
BACKEND_PID="$PROJECT_DIR/data/backend.pid"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

usage() {
  echo "用法: $0 <命令>"
  echo ""
  echo "命令:"
  echo "  build      编译前后端"
  echo "  start      启动全部服务（生产模式）"
  echo "  stop       停止全部服务"
  echo "  restart    重启全部服务"
  echo "  status     查看运行状态"
  echo "  logs       查看后端日志"
  echo "  update     拉取代码 + 构建 + 重启"
  echo "  env        初始化 .env 配置文件"
  echo "  dev        启动开发模式（前后端分别启动）"
  echo "  dev-backend  仅启动后端（开发模式）"
  exit 1
}

# ---- 环境检查 ----
check_deps() {
  for cmd in java mvn npm docker; do
    command -v $cmd &>/dev/null || { err "缺少依赖: $cmd"; exit 1; }
  done
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
  else
    warn ".env 文件不存在，使用默认值。运行 '$0 env' 创建。"
    export JWT_SECRET="${JWT_SECRET:-dev-secret-key-for-local-testing}"
  fi
}

# ---- 构建 ----
build_frontend() {
  info "构建前端..."
  cd "$FRONTEND_DIR"
  npm install --silent
  npm run build
  ok "前端构建完成 → $FRONTEND_DIR/dist"
}

build_backend() {
  info "构建后端..."
  cd "$BACKEND_DIR"
  mvn -q package -DskipTests
  ok "后端构建完成 → $BACKEND_DIR/target/*.jar"
}

build() {
  check_deps
  build_frontend
  build_backend
  ok "全部构建完成"
}

# ---- 生产模式启停 ----
start_infra() {
  info "启动基础设施容器 (MySQL/Redis/MinIO/Mailpit)..."
  cd "$PROJECT_DIR"
  load_env
  docker compose up -d

  info "等待 MySQL 就绪..."
  for i in $(seq 1 30); do
    if docker exec email-system-mysql mysqladmin ping -h 127.0.0.1 -u"${MYSQL_USER:-email_user}" -p"${MYSQL_PASSWORD:-email_password}" --silent 2>/dev/null; then
      ok "MySQL 已就绪"
      return 0
    fi
    sleep 2
  done
  err "MySQL 启动超时"
  return 1
}

start_backend() {
  load_env
  local jar=$(ls -t "$BACKEND_DIR/target/"*.jar 2>/dev/null | head -1)
  if [ -z "$jar" ]; then
    warn "未找到 jar，先执行构建..."
    build_backend
    jar=$(ls -t "$BACKEND_DIR/target/"*.jar 2>/dev/null | head -1)
  fi

  info "启动后端: $jar"
  nohup java -jar "$jar" \
    --spring.profiles.active=prod \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID"

  info "等待后端就绪..."
  for i in $(seq 1 20); do
    if curl -s http://localhost:8080/api/health | grep -q '"status":"up"'; then
      ok "后端已就绪 → http://localhost:8080/api"
      return 0
    fi
    sleep 2
  done
  err "后端启动超时，查看日志: $BACKEND_LOG"
  return 1
}

start_nginx() {
  if grep -q "nginx:" "$PROJECT_DIR/docker-compose.yml" 2>/dev/null; then
    info "启动 Nginx..."
    cd "$PROJECT_DIR"
    docker compose --profile app up -d nginx 2>/dev/null || true
    ok "Nginx 已就绪 → http://localhost"
  fi
}

start() {
  check_deps
  start_infra
  start_backend
  start_nginx
  ok "===== 全部服务已启动 ====="
  status
}

stop() {
  info "停止服务..."

  if [ -f "$BACKEND_PID" ]; then
    kill "$(cat "$BACKEND_PID")" 2>/dev/null && ok "后端已停止" || true
    rm -f "$BACKEND_PID"
  fi
  # 确保占 8080 端口的进程被干掉
  fuser -k 8080/tcp 2>/dev/null || true

  cd "$PROJECT_DIR"
  docker compose --profile app down 2>/dev/null || true
  docker compose down 2>/dev/null || true
  ok "全部服务已停止"
}

restart() {
  stop
  sleep 2
  start
}

# ---- 状态 ----
status() {
  echo ""
  echo -e "${BLUE}═══════════════════════════════════════════${NC}"
  echo -e "${BLUE}  Email System 服务状态${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════${NC}"

  # 后端
  if curl -s http://localhost:8080/api/health 2>/dev/null | grep -q '"status":"up"'; then
    echo -e "  后端 (8080):    ${GREEN}● 运行中${NC}"
  else
    echo -e "  后端 (8080):    ${RED}○ 未运行${NC}"
  fi

  # 前端 / Nginx
  if curl -s -o /dev/null -w '%{http_code}' http://localhost 2>/dev/null | grep -q '200\|304'; then
    echo -e "  前端 (80):      ${GREEN}● 运行中${NC}"
  elif curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 2>/dev/null | grep -q '200\|304'; then
    echo -e "  前端 (5173):    ${GREEN}● 运行中 (dev)${NC}"
  else
    echo -e "  前端:           ${RED}○ 未运行${NC}"
  fi

  # Docker 容器
  for svc in mysql redis minio mailpit; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "email-system-$svc"; then
      echo -e "  $svc:         ${GREEN}● 运行中${NC}"
    else
      echo -e "  $svc:         ${RED}○ 未运行${NC}"
    fi
  done

  echo -e "${BLUE}═══════════════════════════════════════════${NC}"
  echo ""

  # 账号信息
  if curl -s http://localhost:8080/api/health 2>/dev/null | grep -q '"status":"up"'; then
    echo "  Mailpit 界面:  http://localhost:8025"
    echo "  MinIO 控制台:  http://localhost:9001"
  fi
}

# ---- 日志 ----
logs() {
  if [ -f "$BACKEND_LOG" ]; then
    tail -f "$BACKEND_LOG"
  else
    warn "日志文件不存在: $BACKEND_LOG"
    info "使用 docker logs 查看容器日志: docker compose logs -f"
  fi
}

# ---- 更新 ----
update() {
  info "拉取最新代码..."
  cd "$PROJECT_DIR"
  git pull
  build
  restart
  ok "更新完成"
}

# ---- 环境配置 ----
init_env() {
  if [ -f "$ENV_FILE" ]; then
    warn ".env 已存在，不覆盖。编辑: vim $ENV_FILE"
    exit 0
  fi
  cp "$PROJECT_DIR/.env.example" "$ENV_FILE"

  # 生成随机 JWT secret
  local secret=$(dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 | tr -d '\n')
  sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$secret/" "$ENV_FILE"

  ok ".env 已创建: $ENV_FILE"
  warn "请编辑 .env 填入你的配置: JWT_SECRET 已自动生成，还需设置 INIT_ADMIN_PASSWORD 等"
}

# ---- 开发模式 ----
dev_backend() {
  check_deps
  load_env
  info "启动后端 (dev 模式)..."
  cd "$BACKEND_DIR"
  mvn -q spring-boot:run
}

dev_frontend() {
  check_deps
  info "启动前端 (dev 模式)..."
  cd "$FRONTEND_DIR"
  npm run dev
}

dev() {
  dev_backend &
  sleep 5
  dev_frontend
}

# ---- 入口 ----
case "${1:-}" in
  build)        build ;;
  start)        start ;;
  stop)         stop ;;
  restart)      restart ;;
  status)       status ;;
  logs)         logs ;;
  update)       update ;;
  env)          init_env ;;
  dev)          dev ;;
  dev-backend)  dev_backend ;;
  dev-frontend) dev_frontend ;;
  *)            usage ;;
esac
