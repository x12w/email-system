# 部署与 Docker 说明

## 服务组成

| 服务 | 端口 | 说明 |
| --- | --- | --- |
| `nginx` | `80` | 前端静态资源和 API 反向代理 |
| `backend` | `8080` | Spring Boot API |
| `mysql` | `3306` | 业务数据库 |
| `redis` | `6379` | 缓存、验证码、token 黑名单 |
| `minio` | `9000`, `9001` | 对象存储和控制台 |
| `mailpit` | `1025`, `8025` | SMTP 测试服务和 Web UI |

## 本地启动

```bash
cp .env.example .env
docker compose up -d mysql redis minio mailpit
```

后续补齐前后端 Dockerfile 后，可启动完整服务：

```bash
docker compose up -d --build
```

## Nginx 反向代理约定

- `/` 指向前端构建产物。
- `/api/` 转发到后端 `backend:8080`。
- 大附件上传需要配置 `client_max_body_size`。

## 生产注意事项

1. 不要使用 `.env.example` 中的默认密码。
2. JWT 密钥至少 32 字节，生产环境通过密钥管理系统注入。
3. 附件存储建议优先 MinIO，便于扩容和备份。
4. MySQL、Redis、MinIO 数据目录需要挂载到持久化磁盘。
5. Nginx 生产环境启用 HTTPS。

