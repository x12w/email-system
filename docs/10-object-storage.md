# 对象存储与附件管理说明

本文档说明邮件系统中对象存储的用途、MinIO 本地配置、桶规划、附件上传下载流程、权限要求和生产环境建议。

## 存储模式

系统支持两类附件存储模式：

| 模式 | 配置值 | 用途 |
| --- | --- | --- |
| 本地文件系统 | `local` | 开发和小规模部署 |
| MinIO 对象存储 | `minio` | 推荐生产或准生产环境 |

配置项：

```yaml
storage:
  type: ${STORAGE_TYPE:local}
  local:
    root-path: ${STORAGE_LOCAL_ROOT_PATH:./data/uploads}
  minio:
    endpoint: ${MINIO_ENDPOINT:http://localhost:9000}
    access-key: ${MINIO_ROOT_USER:minioadmin}
    secret-key: ${MINIO_ROOT_PASSWORD:minioadmin123}
    bucket: ${MINIO_BUCKET:email-system}
```

## 本地 MinIO

Docker Compose 中的 MinIO 服务：

```yaml
minio:
  image: minio/minio:latest
  ports:
    - "9000:9000"
    - "9001:9001"
  volumes:
    - ./data/uploads:/data
  command: server /data --console-address ":9001"
```

默认访问：

| 服务 | 地址 |
| --- | --- |
| API | `http://localhost:9000` |
| 控制台 | `http://localhost:9001` |

默认账号密码：

```text
minioadmin / minioadmin123
```

生产环境必须替换。

## 桶规划

推荐桶名称：

```text
email-system
```

对象路径建议：

```text
attachments/{userId}/{yyyy}/{MM}/{messageId-or-draftId}/{uuid}-{filename}
```

示例：

```text
attachments/1/2026/06/10001/550e8400-invoice.pdf
```

路径设计原则：

1. 包含用户 ID，便于按用户隔离和排查。
2. 包含年月，避免单目录对象过多。
3. 包含邮件或草稿 ID，便于回溯。
4. 文件名前加 UUID，避免同名覆盖。
5. 原始文件名只作为展示字段，下载时从数据库元数据恢复。

## 附件元数据

附件元数据保存在 `mail_attachment` 表：

| 字段 | 说明 |
| --- | --- |
| `user_id` | 所属用户 |
| `message_id` | 关联邮件，可为空 |
| `original_name` | 原始文件名 |
| `content_type` | MIME 类型 |
| `size_bytes` | 文件大小 |
| `storage_type` | `local` 或 `minio` |
| `storage_path` | 本地路径或对象 key |
| `checksum` | 文件校验值 |
| `deleted` | 软删除标记 |

对象存储只保存二进制文件，权限、归属、展示名、删除状态必须以数据库为准。

## 上传流程

推荐流程：

```text
前端选择文件
  -> POST /api/attachments
  -> 后端校验登录态和文件大小
  -> 计算 checksum
  -> 写入 local 或 MinIO
  -> 保存 mail_attachment 元数据
  -> 返回 attachmentId
  -> 发送邮件时引用 attachmentIds
```

当前接口：

```text
POST /api/attachments
Content-Type: multipart/form-data
字段名：file
```

响应示例：

```json
{
  "id": 1,
  "originalName": "invoice.pdf",
  "contentType": "application/pdf",
  "sizeBytes": 204800,
  "storageType": "minio",
  "downloadUrl": "/api/attachments/1/download"
}
```

## 下载流程

推荐流程：

```text
GET /api/attachments/{id}/download
  -> 校验用户是否拥有附件
  -> 查询 mail_attachment
  -> 从 local 或 MinIO 读取对象
  -> 设置 Content-Disposition
  -> 返回文件流
```

下载权限必须由后端判断，前端不应直接暴露 MinIO 对象地址。

## 删除流程

未发送附件可删除：

```text
DELETE /api/attachments/{id}
```

生产建议：

1. 先将数据库 `deleted` 置为 `1`。
2. 后台异步清理对象存储文件。
3. 对已发送邮件附件保留审计记录。
4. 对清理失败对象写入重试队列。

## 文件限制建议

| 限制项 | 建议值 |
| --- | --- |
| 单文件大小 | 25 MB 或按邮件服务限制配置 |
| 单封邮件附件总大小 | 50 MB |
| 文件名长度 | 255 字符以内 |
| 禁止类型 | `.exe`, `.bat`, `.cmd`, `.scr`, `.js` 等高危类型 |
| 图片预览 | 限制在可信 MIME 类型 |
| checksum | SHA-256 |

## MinIO 权限建议

生产环境建议：

1. 禁止使用 root 账号作为应用账号。
2. 为后端创建专用 access key。
3. 只授予目标桶的读写权限。
4. 管理控制台限制内网访问。
5. 启用 HTTPS 或通过网关终止 TLS。
6. 不为附件桶开启公开读。
7. 下载统一走后端鉴权接口。

## 备份和生命周期

建议策略：

| 对象类型 | 生命周期 |
| --- | --- |
| 草稿附件 | 草稿删除后 7 天清理 |
| 未发送临时附件 | 24 小时后清理 |
| 已发送/已接收附件 | 跟随邮件保留策略 |
| 垃圾邮件附件 | 按安全策略隔离或延迟清理 |

备份建议：

1. 对 MinIO 数据目录做定期快照。
2. 生产环境使用对象复制或异地备份。
3. 数据库和对象存储备份时间点应尽量一致。
4. 定期校验数据库 `storage_path` 对应对象是否存在。

## 巡检脚本建议

建议后续在 `scripts/` 中新增巡检脚本：

```text
scripts/storage-check.sh
scripts/storage-orphan-clean.sh
scripts/storage-backup.sh
```

巡检项：

1. 桶是否存在。
2. 后端 access key 是否可读写。
3. 数据库附件记录是否存在对应对象。
4. 对象存储中是否存在孤儿文件。
5. 附件总大小和增长速度。

## 常见问题

### 1. MinIO 控制台无法打开

确认容器运行：

```bash
docker compose ps minio
```

访问：

```text
http://localhost:9001
```

### 2. 上传接口返回失败

检查：

1. 是否已登录。
2. 请求字段名是否为 `file`。
3. 文件大小是否超过限制。
4. `storage.type` 是否配置正确。
5. MinIO endpoint、账号、密码和 bucket 是否正确。

### 3. 下载附件没有原始文件名

后端需要设置：

```text
Content-Disposition: attachment; filename="<originalName>"
```

原始文件名应读取 `mail_attachment.original_name`。

### 4. 对象存在但数据库记录缺失

这是孤儿对象。建议先导出清单人工确认，再按生命周期规则清理。

### 5. 数据库记录存在但对象缺失

这是数据一致性问题。需要：

1. 标记附件异常。
2. 禁止继续下载。
3. 从备份恢复对象。
4. 写入审计记录。
