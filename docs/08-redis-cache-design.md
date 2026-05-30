# Email System Redis 缓存设计

> Redis 7.2 | 数据源：MySQL 8.0

## 1. 键命名规范

所有 Redis 键遵循以下模式：

```
mail:{模块}:{实体}:{标识符}
```

| 模块 | 实体 | 键示例 | 值类型 | 说明 |
|--------|--------|-------------|------------|-------------|
| `mail` | 邮件列表 | `mail:message:list:{user_id}:{folder_id}` | 有序集合 | 按文件夹分页的邮件列表 |
| `mail` | 未读数 | `mail:unread:counts:{user_id}` | 哈希 | 按 folder_id 存储的每用户未读数 |
| `mail` | 文件夹统计 | `mail:folder:stats:{user_id}` | 哈希 | 按 folder_id 存储的每用户文件夹统计 |
| `mail` | 邮件详情 | `mail:message:detail:{message_id}` | 字符串（JSON） | 邮件完整数据 |
| `session` | 用户会话 | `session:user:{user_id}` | 字符串（JSON） | 用户信息与权限列表 |
| `ratelimit` | 登录限流 | `ratelimit:login:{ip_address}` | 有序集合 | 按 IP 的滑动窗口限流 |

---

## 2. 邮件列表缓存（按文件夹分页）

**数据结构：** 有序集合
**键：** `mail:message:list:{user_id}:{folder_id}`
**Score（分数）：** `received_at` 转换为毫秒级时间戳
**Member（成员）：** 邮件摘要 JSON（id、subject、from_address、from_name、read_flag、star_flag、attachment_count、received_at）
**过期时间：** 30 分钟

### 写入（新邮件到达或 MUA 同步时）

```redis
-- 将邮件添加到对应文件夹的有序集合中
ZADD mail:message:list:1001:5 1715961600000 '{"id":5001,"subject":"Meeting Notes","from_address":"alice@example.com","from_name":"Alice","read_flag":0,"star_flag":0,"attachment_count":2,"received_at":"2026-05-17T12:00:00+08:00"}'

-- 重置过期时间
EXPIRE mail:message:list:1001:5 1800
```

### 读取（分页列表，最新在前）

```redis
-- 第 1 页：获取最新 20 封邮件（score 从高到低 = 最新在前）
ZREVRANGEBYSCORE mail:message:list:1001:5 +inf -inf LIMIT 0 20

-- 第 2 页：获取第 21-40 封邮件
ZREVRANGEBYSCORE mail:message:list:1001:5 +inf -inf LIMIT 20 20

-- 获取文件夹内邮件总数
ZCARD mail:message:list:1001:5
```

### 删除单封邮件（删除操作时）

```redis
-- 按成员值删除（需要精确匹配 JSON 字符串）
ZREM mail:message:list:1001:5 '{"id":5001,...}'
```

### 裁剪旧数据（清理时，仅保留最近 1000 条）

```redis
ZREMRANGEBYRANK mail:message:list:1001:5 0 -1001
```

---

## 3. 未读计数缓存

**数据结构：** 哈希
**键：** `mail:unread:counts:{user_id}`
**字段：** `folder_id` → 未读数量（整数）
**过期时间：** 5 分钟

### 写入（已读/未读切换或新邮件到达后）

```redis
-- 同步后全量刷新
HSET mail:unread:counts:1001 5 12 7 0 9 3

-- 新邮件到达时递增
HINCRBY mail:unread:counts:1001 5 1

-- 标记已读时递减
HINCRBY mail:unread:counts:1001 5 -1

EXPIRE mail:unread:counts:1001 300
```

### 读取

```redis
-- 获取指定文件夹的未读数
HGET mail:unread:counts:1001 5

-- 获取所有文件夹的未读数
HGETALL mail:unread:counts:1001
```

---

## 4. 用户会话缓存

**数据结构：** 字符串（JSON）
**键：** `session:user:{user_id}`
**值：** 包含用户信息、角色编码和权限列表的 JSON
**过期时间：** 24 小时（与 JWT 过期时间对齐）

### 写入（登录 / Token 刷新时）

```redis
SET session:user:1001 '{"user_id":1001,"username":"zhangsan","display_name":"Zhang San","email":"zhangsan@example.com","avatar_url":"https://cdn.example.com/avatars/1001.jpg","status":1,"roles":["user"],"permissions":["mail:read","mail:send","contact:read"]}' EX 86400
```

### 读取（每次请求经过认证中间件时）

```redis
GET session:user:1001
```

### 删除（退出登录 / 会话失效时）

```redis
DEL session:user:1001
```

---

## 5. 文件夹统计缓存

**数据结构：** 哈希
**键：** `mail:folder:stats:{user_id}`
**字段：** `folder_id` → JSON `{"total_count":N,"unread_count":N,"name":"文件夹名称","type":"inbox"}`
**过期时间：** 10 分钟

### 写入（同步后全量刷新）

```redis
HSET mail:folder:stats:1001 5 '{"total_count":245,"unread_count":12,"name":"收件箱","type":"inbox"}'
HSET mail:folder:stats:1001 7 '{"total_count":89,"unread_count":0,"name":"已发送","type":"sent"}'
HSET mail:folder:stats:1001 9 '{"total_count":3,"unread_count":3,"name":"草稿箱","type":"draft"}'

EXPIRE mail:folder:stats:1001 600
```

### 读取（侧边栏文件夹渲染）

```redis
-- 获取单个文件夹的统计信息
HGET mail:folder:stats:1001 5

-- 获取所有文件夹的统计信息
HGETALL mail:folder:stats:1001
```

### 部分更新（新邮件到达时递增 total_count）

```redis
-- 需要使用 Lua 脚本实现原子性的 JSON 原地更新，
-- 或者直接令缓存失效，让下一次读取触发数据库回源刷新
DEL mail:folder:stats:1001
```

---

## 6. 邮件详情缓存

**数据结构：** 字符串（JSON）
**键：** `mail:message:detail:{message_id}`
**值：** 邮件完整 JSON（邮件头、正文、收件人、附件元数据）
**过期时间：** 1 小时

### 写入（从数据库读取邮件时）

```redis
SET mail:message:detail:5001 '{"id":5001,"from_address":"alice@example.com","from_name":"Alice","subject":"会议纪要","content":"<html>...</html>","content_type":"html","sent_at":"2026-05-17T11:55:00+08:00","received_at":"2026-05-17T12:00:00+08:00","read_flag":0,"star_flag":0,"attachments":[{"id":201,"original_name":"notes.pdf","size_bytes":102400,"content_type":"application/pdf"}],"recipients":[{"type":"to","email_address":"bob@example.com","display_name":"Bob"}]}' EX 3600
```

### 读取（邮件详情页面）

```redis
GET mail:message:detail:5001
```

### 更新 read_flag（用户打开邮件后）

```redis
-- 方案 A：令缓存失效，让下一次读取从数据库重建
DEL mail:message:detail:5001

-- 方案 B：使用 Lua 脚本实现 读取 → 修改 JSON → 写回 的原子操作
```

---

## 7. 登录限流

**数据结构：** 有序集合（滑动窗口）
**键：** `ratelimit:login:{ip_address}`
**Score（分数）：** 当前毫秒级时间戳（member 值可任意，此处使用时间戳作为唯一成员）
**窗口：** 15 分钟
**限制：** 每个 IP 每 15 分钟最多 20 次尝试

### 检查并记录尝试（Lua 脚本）

```lua
-- Lua 脚本（原子性地完成检查 + 记录）
-- KEYS[1] = ratelimit:login:{ip}
-- ARGV[1] = 当前毫秒时间戳
-- ARGV[2] = 窗口起始毫秒时间戳（now - 15 * 60 * 1000）
-- ARGV[3] = 最大尝试次数（20）

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local max_attempts = tonumber(ARGV[3])

-- 移除滑动窗口之外的过期条目
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

-- 统计窗口内剩余条目数
local count = redis.call('ZCARD', key)

if count >= max_attempts then
    return 0  -- 触发限流
end

-- 记录本次尝试
redis.call('ZADD', key, now, now)
redis.call('EXPIRE', key, 900)  -- 15 分钟过期
return 1  -- 允许通过
```

### 原始 Redis 命令（非原子操作示意）

```redis
-- 移除过期条目（15 分钟之前的）
ZREMRANGEBYSCORE ratelimit:login:192.168.1.100 0 1715960700000

-- 统计窗口内的尝试次数
ZCARD ratelimit:login:192.168.1.100

-- 如果次数 < 20，记录本次尝试
ZADD ratelimit:login:192.168.1.100 1715961600000 1715961600000
EXPIRE ratelimit:login:192.168.1.100 900
```

---

## 8. 缓存失效策略表

| 事件 | 需要失效的键 | 操作 |
|-------|--------------------|--------|
| **新邮件到达** | `mail:message:list:{uid}:{fid}`（重新排序）、`mail:unread:counts:{uid}`（HINCRBY +1）、`mail:folder:stats:{uid}`（DEL） | 部分更新或删除 |
| **标记邮件已读** | `mail:message:detail:{mid}`（DEL 或更新 JSON）、`mail:message:list:{uid}:{fid}`（更新 member JSON）、`mail:unread:counts:{uid}`（HINCRBY -1） | DEL 或部分更新 |
| **删除邮件（移入回收站）** | `mail:message:list:{uid}:{fid}`（ZREM）、`mail:message:detail:{mid}`（DEL）、`mail:folder:stats:{uid}`（DEL） | 从缓存中删除 |
| **移动邮件到其他文件夹** | `mail:message:list:{uid}:{src_fid}`（ZREM）、`mail:message:list:{uid}:{dst_fid}`（ZADD 或 DEL）、`mail:folder:stats:{uid}`（DEL） | 从源文件夹移除，目标文件夹失效 |
| **文件夹同步完成** | `mail:folder:stats:{uid}`（DEL）、`mail:unread:counts:{uid}`（DEL）、各文件夹 `mail:message:list:{uid}:{fid}`（DEL） | 全量失效，下次读取时重建 |
| **用户退出登录** | `session:user:{uid}`（DEL） | 删除会话 |
| **用户权限变更** | `session:user:{uid}`（DEL） | 删除会话，下次登录时获取新权限 |
| **账号状态变更** | `session:user:{uid}`（DEL） | 强制重新登录 |
| **附件上传** | `mail:message:detail:{mid}`（DEL） | 失效以刷新附件列表 |
| **联系人创建/更新/删除** | 无（联系人采用直接读取或独立短过期时间缓存） | 不适用 |

### 失效策略：Cache-Aside（旁路缓存 / 懒加载）

```
1. 写入：应用先更新数据库，然后删除/失效受影响的缓存键。
2. 读取：应用先查缓存。缓存未命中（MISS）时，从数据库加载并回填缓存。
3. 此策略避免了写入时的缓存击穿，并保持缓存与数据库的一致性。
```

---

## 9. 缓存穿透防护

缓存穿透是指客户端请求数据库中不存在的数据。如果不加防护，每次请求都会绕过缓存直接打到数据库。

### 解决方案：空对象缓存

对于不存在/空结果的数据，缓存一个哨兵值，并设置较短的过期时间。

```redis
-- 数据库查询某邮件 ID 返回空结果集后
SET mail:message:detail:99999 "NULL" EX 30

-- 数据库查询某文件夹返回空列表后
ZADD mail:message:list:1001:999 0 "NULL"
EXPIRE mail:message:list:1001:999 30
```

### 应用层处理逻辑

```
1. 缓存命中但值为 "NULL" → 立即返回 404 / 空列表
2. 30 秒的过期时间可防止不存在的数据持续冲击数据库
3. 当数据被实际创建时，写入路径会删除该空缓存条目
```

### 布隆过滤器（可选，适用于大规模部署）

对于超大规模部署，可以在 API 网关层使用布隆过滤器，在不存在的邮件 ID 请求到达 Redis 之前就将其拦截：

```redis
-- 需要安装 RedisBloom 模块
BF.RESERVE mail:message:exists 0.01 1000000
BF.ADD mail:message:exists 5001
BF.EXISTS mail:message:exists 99999  -- 返回 0（确定不存在）
```

---

## 10. 缓存预热策略

缓存预热通过在用户登录时预填充热点缓存键，降低冷启动时的延迟影响。

### 触发时机：登录成功

在认证成功之后、向客户端返回响应之前：

```
1. 加载用户会话 → SET session:user:{uid}
2. 加载文件夹列表 → HSET mail:folder:stats:{uid}
3. 加载未读计数 → HSET mail:unread:counts:{uid}
4. 加载收件箱第一页 → ZADD mail:message:list:{uid}:{inbox_fid}
```

### 实现伪代码

```
async function warmCacheOnLogin(userId) {
    // 1. 用户会话（认证流程中已完成设置）
    // 2. 文件夹统计
    const folders = await db.query(
        'SELECT id, name, type, total_count, unread_count FROM mail_folder WHERE user_id = ? AND deleted = 0',
        [userId]
    );
    const folderPipeline = redis.pipeline();
    const unreadPipeline = redis.pipeline();
    for (const f of folders) {
        folderPipeline.hset(
            `mail:folder:stats:${userId}`,
            f.id,
            JSON.stringify({ total_count: f.total_count, unread_count: f.unread_count, name: f.name, type: f.type })
        );
        unreadPipeline.hset(`mail:unread:counts:${userId}`, f.id, f.unread_count);
    }
    folderPipeline.expire(`mail:folder:stats:${userId}`, 600);
    unreadPipeline.expire(`mail:unread:counts:${userId}`, 300);
    await Promise.all([folderPipeline.exec(), unreadPipeline.exec()]);

    // 3. 收件箱首页（定位收件箱文件夹，加载最新 20 封邮件）
    const inbox = folders.find(f => f.type === 'inbox');
    if (inbox) {
        const messages = await db.query(
            'SELECT id, subject, from_address, from_name, read_flag, star_flag, attachment_count, received_at FROM mail_message WHERE user_id = ? AND folder_id = ? AND deleted = 0 AND deleted_flag = 0 ORDER BY received_at DESC LIMIT 20',
            [userId, inbox.id]
        );
        if (messages.length > 0) {
            const zaddPipeline = redis.pipeline();
            for (const m of messages) {
                zaddPipeline.zadd(
                    `mail:message:list:${userId}:${inbox.id}`,
                    new Date(m.received_at).getTime(),
                    JSON.stringify(m)
                );
            }
            zaddPipeline.expire(`mail:message:list:${userId}:${inbox.id}`, 1800);
            await zaddPipeline.exec();
        }
    }
}
```

### 预热键清单

| 优先级 | 键模式 | 是否预热 | 原因 |
|----------|-------------|-----------|-----------|
| P0 | `session:user:{uid}` | 是 | 每个认证请求都需要 |
| P1 | `mail:folder:stats:{uid}` | 是 | 登录后侧边栏渲染需要 |
| P1 | `mail:unread:counts:{uid}` | 是 | 登录后角标计数需要 |
| P2 | `mail:message:list:{uid}:{inbox}` | 是 | 收件箱是默认视图，避免冷加载延迟 |
| P3 | `mail:message:list:{uid}:{other}` | 否 | 用户导航到其他文件夹时懒加载 |
| P3 | `mail:message:detail:{mid}` | 否 | 用户打开具体邮件时懒加载 |

---

## 总结：过期时间参考表

| 缓存类型 | 键模式 | 过期时间 | 原因 |
|-------|-------------|-----|-----------|
| 邮件列表 | `mail:message:list:{uid}:{fid}` | 30 分钟 | 平衡数据新鲜度与数据库卸载；新邮件到达时主动失效 |
| 未读计数 | `mail:unread:counts:{uid}` | 5 分钟 | 需要保持足够新鲜以确保角标准确显示 |
| 用户会话 | `session:user:{uid}` | 24 小时 | 与 JWT 过期时间对齐 |
| 文件夹统计 | `mail:folder:stats:{uid}` | 10 分钟 | 侧边栏信息变更频率较低 |
| 邮件详情 | `mail:message:detail:{mid}` | 1 小时 | 邮件内容一旦接收后不可变 |
| 登录限流 | `ratelimit:login:{ip}` | 15 分钟（窗口） | 滑动窗口用于暴力破解防护 |
| 空值哨兵 | （任意） | 30 秒 | 短周期以便真实数据创建后能快速覆盖 |
