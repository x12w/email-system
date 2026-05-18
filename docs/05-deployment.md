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
| `intelligence-plugin` | 无固定端口 | Python 智能分析插件构建或运行环境 |

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
6. 智能分析插件动态库需要按操作系统单独构建，并通过校验和确认未被篡改。
7. Python 插件异常不能阻塞邮件收发主链路，生产环境必须启用超时、熔断和降级。

## 智能插件部署

推荐在 CI 中构建 Python 插件产物，并发布到：

```text
plugins/intelligence/native/linux/libmail_intelligence.so
plugins/intelligence/native/windows/mail_intelligence.dll
plugins/intelligence/native/darwin/libmail_intelligence.dylib
```

后端通过配置读取插件路径：

```yaml
intelligence:
  plugin:
    enabled: true
    name: python-mail-intelligence
    version: 0.1.0
    artifact-path: ./plugins/intelligence/native/linux/libmail_intelligence.so
    timeout-ms: 2000
```
