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
  echo "  check      检查依赖和配置"
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
  local missing=()
  for cmd in java mvn npm docker curl; do
    command -v $cmd &>/dev/null || missing+=("$cmd")
  done
  if [ ${#missing[@]} -gt 0 ]; then
    err "缺少以下依赖: ${missing[*]}"
    echo ""
    echo "  安装指引:"
    for dep in "${missing[@]}"; do
      case $dep in
        java)  echo "    java : dnf install java-17-openjdk 或 apt install openjdk-17-jdk" ;;
        mvn)   echo "    mvn  : dnf install maven 或 apt install maven" ;;
        npm)   echo "    npm  : dnf install nodejs 或 apt install nodejs npm" ;;
        docker)echo "    docker: https://docs.docker.com/engine/install/" ;;
        curl)  echo "    curl : dnf install curl 或 apt install curl" ;;
      esac
    done
    exit 1
  fi
  ok "所有依赖已满足 (java, mvn, npm, docker, curl)"
}

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
  else
    warn ".env 文件不存在，运行 '$0 env' 创建。"
  fi
  # JWT_SECRET 为空时自动生成临时密钥，仅当前会话有效
  if [ -z "${JWT_SECRET:-}" ]; then
    JWT_SECRET=$(dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 | tr -d '\n' | tr -d '/+=' | head -c 32)
    warn "JWT_SECRET 未设置，已自动生成临时密钥。运行 '$0 env' 创建永久 .env 文件。"
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

  # 将 .env 中的全部变量转为 -D JVM 参数
  local env_opts=()
  if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
      # 跳过注释和空行
      [[ "$key" =~ ^# ]] && continue
      [[ -z "$key" ]] && continue
      # 去掉 value 中的行内注释
      value="${value%%#*}"
      value="${value//\"/}"
      value="${value//\'/}"
      [ -n "${!key:-}" ] && env_opts+=("-D$key=${!key}")
    done < "$ENV_FILE"
  fi

  info "启动后端: $jar"
  nohup java "${env_opts[@]}" -jar "$jar" \
    > "$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID"

  info "等待后端就绪..."
  for i in $(seq 1 30); do
    if curl -s http://localhost:8080/api/health | grep -q '"status":"up"'; then
      ok "后端已就绪 → http://localhost:8080/api"
      return 0
    fi
    sleep 3
  done
  err "后端启动超时，查看日志: $BACKEND_LOG"
  tail -20 "$BACKEND_LOG"
  return 1
}

start_nginx() {
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q email-system-nginx && return 0

  info "启动 Nginx..."
  local dist_dir="$FRONTEND_DIR/dist"
  if [ ! -d "$dist_dir" ]; then
    warn "前端未构建，跳过 Nginx"
    return 0
  fi

  local domain="${DOMAIN:-panel.x12w.com}"
  local cert_dir="/etc/letsencrypt/live/$domain"
  local ssl_block=""
  local extra_mounts=""
  if [ -f "$cert_dir/fullchain.pem" ]; then
    ssl_block="
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;"
    extra_mounts="-v $cert_dir/fullchain.pem:/etc/nginx/certs/fullchain.pem:ro
      -v $cert_dir/privkey.pem:/etc/nginx/certs/privkey.pem:ro"
    ok "检测到 SSL 证书，启用 HTTPS"
  fi

  cat > /tmp/nginx-email.conf << NGINX_EOF
server {
    listen 80;
    ${ssl_block:+listen 443 ssl;}
    ${ssl_block:+ssl_certificate /etc/nginx/certs/fullchain.pem;}
    ${ssl_block:+ssl_certificate_key /etc/nginx/certs/privkey.pem;}
    root /usr/share/nginx/html;
    index index.html;
    client_max_body_size 50m;
    location / { try_files \$uri \$uri/ /index.html; }
    location /api/ {
        proxy_pass http://host.docker.internal:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX_EOF

  docker rm -f email-system-nginx 2>/dev/null || true
  docker run -d --name email-system-nginx \
    --add-host=host.docker.internal:host-gateway \
    -p 80:80 \
    $([ -n "$ssl_block" ] && echo "-p 443:443") \
    -v "$dist_dir:/usr/share/nginx/html:ro" \
    -v /tmp/nginx-email.conf:/etc/nginx/conf.d/default.conf:ro \
    $extra_mounts \
    nginx:1.27-alpine >/dev/null 2>&1
  info "等待 Nginx 就绪..."
  for i in $(seq 1 10); do
    if curl -s -o /dev/null -w '%{http_code}' http://localhost 2>/dev/null | grep -q '200\|301\|304'; then
      ok "Nginx 已就绪 → http://localhost"
      return 0
    fi
    sleep 1
  done
  warn "Nginx 可能未完全就绪，请检查: docker logs email-system-nginx"
  return 1
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
  fuser -k 8080/tcp 2>/dev/null || true

  docker rm -f email-system-nginx 2>/dev/null && ok "Nginx 已停止" || true

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
  if curl -s -o /dev/null -w '%{http_code}' http://localhost 2>/dev/null | grep -q '200\|301\|304'; then
    echo -e "  前端 (80):      ${GREEN}● 运行中${NC}"
  elif curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 2>/dev/null | grep -q '200\|301\|304'; then
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
  local target="${2:-backend}"
  local lines="${3:-50}"
  case "$target" in
    backend|be)
      if [ -f "$BACKEND_LOG" ]; then
        tail -${lines} "$BACKEND_LOG"
        echo ""
        info "实时日志: tail -f $BACKEND_LOG"
      else
        warn "后端日志不存在: $BACKEND_LOG"
      fi
      ;;
    nginx|ng)
      docker logs --tail "$lines" email-system-nginx 2>/dev/null || warn "Nginx 容器未运行"
      ;;
    mysql|db)
      docker logs --tail "$lines" email-system-mysql 2>/dev/null || warn "MySQL 容器未运行"
      ;;
    all)
      echo -e "${BLUE}═══ 后端日志 (最近 $lines 行) ═══${NC}"
      tail -${lines} "$BACKEND_LOG" 2>/dev/null
      echo ""
      echo -e "${BLUE}═══ Nginx 日志 ═══${NC}"
      docker logs --tail 10 email-system-nginx 2>/dev/null
      ;;
    *)
      echo "用法: $0 logs [backend|nginx|mysql|all] [行数]"
      ;;
  esac
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
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$secret|" "$ENV_FILE"

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
check() {
  echo ""
  echo -e "${BLUE}═══ 环境检查 ═══${NC}"
  check_deps
  echo ""
  echo -e "${BLUE}═══ 配置文件 ═══${NC}"
  if [ -f "$ENV_FILE" ]; then
    ok ".env 存在"
    load_env
    [ -n "${JWT_SECRET:-}" ] && ok "JWT_SECRET 已设置" || warn "JWT_SECRET 未设置"
  else
    warn ".env 不存在，运行 '$0 env' 创建"
  fi
  echo ""
  echo -e "${BLUE}═══ 磁盘空间 ═══${NC}"
  df -h "$PROJECT_DIR" | tail -1
}

case "${1:-}" in
  check)        check ;;
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
