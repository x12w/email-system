# Redis Cache Design for Email System

> Redis 7.2 | Data source of truth: MySQL 8.0

## 1. Key Naming Convention

All Redis keys follow the pattern:

```
mail:{module}:{entity}:{identifier}
```

| Module | Entity | Key Example | Value Type | Description |
|--------|--------|-------------|------------|-------------|
| `mail` | message list | `mail:message:list:{user_id}:{folder_id}:{page}` | Sorted Set | Paged message list per folder |
| `mail` | unread count | `mail:unread:counts:{user_id}` | Hash | Per-user unread counts keyed by folder_id |
| `mail` | folder stats | `mail:folder:stats:{user_id}` | Hash | Per-user folder statistics keyed by folder_id |
| `mail` | message detail | `mail:message:detail:{message_id}` | String (JSON) | Full message data |
| `session` | user session | `session:user:{user_id}` | String (JSON) | User info + permissions |
| `ratelimit` | login | `ratelimit:login:{ip_address}` | Sorted Set | Sliding-window rate limit per IP |

---

## 2. Mail List Cache (per folder with pagination)

**Data structure:** Sorted Set  
**Key:** `mail:message:list:{user_id}:{folder_id}`  
**Score:** `received_at` as epoch milliseconds  
**Member:** Message summary JSON (id, subject, from_address, from_name, read_flag, star_flag, attachment_count, received_at)  
**TTL:** 30 minutes

### Write (on new mail arrival or MUA sync)

```redis
-- Add message to folder's sorted set
ZADD mail:message:list:1001:5 1715961600000 '{"id":5001,"subject":"Meeting Notes","from_address":"alice@example.com","from_name":"Alice","read_flag":0,"star_flag":0,"attachment_count":2,"received_at":"2024-05-17T12:00:00Z"}'

-- Reset TTL
EXPIRE mail:message:list:1001:5 1800
```

### Read (paginated listing, newest first)

```redis
-- Page 1: 20 most recent messages (score high→low = newest first)
ZREVRANGEBYSCORE mail:message:list:1001:5 +inf -inf LIMIT 0 20

-- Page 2: messages 21-40
ZREVRANGEBYSCORE mail:message:list:1001:5 +inf -inf LIMIT 20 20

-- Get total count in folder
ZCARD mail:message:list:1001:5
```

### Remove a single message (on delete)

```redis
-- Remove by member value (exact JSON match)
ZREM mail:message:list:1001:5 '{"id":5001,...}'
```

### Trim old entries (on clean-up, keep last 1000)

```redis
ZREMRANGEBYRANK mail:message:list:1001:5 0 -1001
```

---

## 3. Unread Count Cache

**Data structure:** Hash  
**Key:** `mail:unread:counts:{user_id}`  
**Fields:** `folder_id` -> unread count (integer)  
**TTL:** 5 minutes

### Write (after read/unread toggle or new mail)

```redis
-- Full refresh after sync
HSET mail:unread:counts:1001 5 12 7 0 9 3

-- Increment on new mail arrival
HINCRBY mail:unread:counts:1001 5 1

-- Decrement on mark-as-read
HINCRBY mail:unread:counts:1001 5 -1

EXPIRE mail:unread:counts:1001 300
```

### Read

```redis
-- Get unread count for a specific folder
HGET mail:unread:counts:1001 5

-- Get all folder unread counts
HGETALL mail:unread:counts:1001
```

---

## 4. User Session Cache

**Data structure:** String (JSON)  
**Key:** `session:user:{user_id}`  
**Value:** JSON containing user info, role codes, and permission list  
**TTL:** 24 hours (aligned with JWT expiration)

### Write (on login / token refresh)

```redis
SET session:user:1001 '{"user_id":1001,"username":"zhangsan","display_name":"Zhang San","email":"zhangsan@example.com","avatar_url":"https://cdn.example.com/avatars/1001.jpg","status":1,"roles":["user"],"permissions":["mail:read","mail:send","contact:read"]}' EX 86400
```

### Read (auth middleware on every request)

```redis
GET session:user:1001
```

### Delete (on logout / session invalidation)

```redis
DEL session:user:1001
```

---

## 5. Folder Statistics Cache

**Data structure:** Hash  
**Key:** `mail:folder:stats:{user_id}`  
**Fields:** `folder_id` -> JSON `{"total_count":N,"unread_count":N,"name":"folder_name","type":"inbox"}`  
**TTL:** 10 minutes

### Write (full refresh after sync)

```redis
HSET mail:folder:stats:1001 5 '{"total_count":245,"unread_count":12,"name":"Inbox","type":"inbox"}'
HSET mail:folder:stats:1001 7 '{"total_count":89,"unread_count":0,"name":"Sent","type":"sent"}'
HSET mail:folder:stats:1001 9 '{"total_count":3,"unread_count":3,"name":"Drafts","type":"draft"}'

EXPIRE mail:folder:stats:1001 600
```

### Read (folder sidebar rendering)

```redis
-- Get stats for a single folder
HGET mail:folder:stats:1001 5

-- Get stats for all folders
HGETALL mail:folder:stats:1001
```

### Partial update (increment total_count on new mail)

```redis
-- Requires Lua script for atomic JSON-in-place update,
-- or invalidate and let next read trigger DB refresh
DEL mail:folder:stats:1001
```

---

## 6. Message Detail Cache

**Data structure:** String (JSON)  
**Key:** `mail:message:detail:{message_id}`  
**Value:** Full message JSON (headers, content, recipients, attachment metadata)  
**TTL:** 1 hour

### Write (on message fetch from DB)

```redis
SET mail:message:detail:5001 '{"id":5001,"from_address":"alice@example.com","from_name":"Alice","subject":"Meeting Notes","content":"<html>...</html>","content_type":"html","sent_at":"2024-05-17T11:55:00Z","received_at":"2024-05-17T12:00:00Z","read_flag":0,"star_flag":0,"attachments":[{"id":201,"original_name":"notes.pdf","size_bytes":102400,"content_type":"application/pdf"}],"recipients":[{"type":"to","email_address":"bob@example.com","display_name":"Bob"}]}' EX 3600
```

### Read (message detail view)

```redis
GET mail:message:detail:5001
```

### Update read_flag (after user opens message)

```redis
-- Option A: Invalidate, let next read rebuild from DB
DEL mail:message:detail:5001

-- Option B: Lua script to read → modify JSON → write back atomically
```

---

## 7. Login Rate Limiting

**Data structure:** Sorted Set (sliding window)  
**Key:** `ratelimit:login:{ip_address}`  
**Score:** Current epoch milliseconds (member value is arbitrary, using timestamp as unique member)  
**Window:** 15 minutes  
**Limit:** 20 attempts per 15 minutes per IP

### Check and record attempt

```lua
-- Lua script (atomic check + record)
-- KEYS[1] = ratelimit:login:{ip}
-- ARGV[1] = current_timestamp_ms
-- ARGV[2] = window_start_ms (now - 15 * 60 * 1000)
-- ARGV[3] = max_attempts (20)

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local max_attempts = tonumber(ARGV[3])

-- Remove entries outside the sliding window
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

-- Count remaining entries in window
local count = redis.call('ZCARD', key)

if count >= max_attempts then
    return 0  -- rate limited
end

-- Record this attempt
redis.call('ZADD', key, now, now)
redis.call('EXPIRE', key, 900)  -- 15 min TTL
return 1  -- allowed
```

### Raw Redis commands (non-atomic illustration)

```redis
-- Remove expired entries (older than 15 min)
ZREMRANGEBYSCORE ratelimit:login:192.168.1.100 0 1715960700000

-- Count attempts in window
ZCARD ratelimit:login:192.168.1.100

-- If count < 20, record this attempt
ZADD ratelimit:login:192.168.1.100 1715961600000 1715961600000
EXPIRE ratelimit:login:192.168.1.100 900
```

---

## 8. Cache Invalidation Table

| Event | Keys to Invalidate | Action |
|-------|--------------------|--------|
| **New mail received** | `mail:message:list:{uid}:{fid}` (re-sort), `mail:unread:counts:{uid}` (HINCRBY +1), `mail:folder:stats:{uid}` (DEL) | Partially update or delete |
| **Mark mail as read** | `mail:message:detail:{mid}` (DEL or update JSON), `mail:message:list:{uid}:{fid}` (update member JSON), `mail:unread:counts:{uid}` (HINCRBY -1) | DEL or partial update |
| **Delete mail (trash)** | `mail:message:list:{uid}:{fid}` (ZREM), `mail:message:detail:{mid}` (DEL), `mail:folder:stats:{uid}` (DEL) | Delete from caches |
| **Move mail to another folder** | `mail:message:list:{uid}:{src_fid}` (ZREM), `mail:message:list:{uid}:{dst_fid}` (ZADD or DEL), `mail:folder:stats:{uid}` (DEL) | Remove from source, invalidate destination |
| **Folder sync complete** | `mail:folder:stats:{uid}` (DEL), `mail:unread:counts:{uid}` (DEL), per-folder `mail:message:list:{uid}:{fid}` (DEL) | Full invalidation, rebuild on next read |
| **User logout** | `session:user:{uid}` (DEL) | Delete session |
| **User permission change** | `session:user:{uid}` (DEL) | Delete session so next login picks up new permissions |
| **Account status change** | `session:user:{uid}` (DEL) | Force re-login |
| **Attachment upload** | `mail:message:detail:{mid}` (DEL) | Invalidate to refresh attachment list |
| **Contact created/updated/deleted** | None (contacts are read-direct or have separate short-TTL cache) | N/A |

### Invalidation strategy: Cache-Aside (Lazy Loading)

```
1. Write: Application updates DB first, then DELETES/invalidates affected cache keys.
2. Read: Application checks cache. On MISS, loads from DB and populates cache.
3. This avoids cache-stampede on writes and keeps cache/Db consistent.
```

---

## 9. Cache Penetration Prevention

Cache penetration occurs when a client requests data that does not exist in the database.
Without protection, each request bypasses the cache and hits the database directly.

### Solution: Null Object Cache

For empty/non-existent results, cache a sentinel value with a short TTL.

```redis
-- After DB query returns empty result set for a message ID
SET mail:message:detail:99999 "NULL" EX 30

-- After DB query returns empty folder listing
ZADD mail:message:list:1001:999 0 "NULL"
EXPIRE mail:message:list:1001:999 30
```

### Application-level handling

```
1. On cache hit with value "NULL" → return 404 / empty list immediately
2. TTL of 30 seconds prevents a non-existent resource from hammering the DB
3. When the resource is actually created, the write path DELETEs the null cache entry
```

### Bloom Filter (optional, for high-scale deploy)

For very large deployments, a Bloom Filter at the API gateway layer can reject
requests for non-existent message IDs before they even reach Redis:

```redis
-- RedisBloom module required
BF.RESERVE mail:message:exists 0.01 1000000
BF.ADD mail:message:exists 5001
BF.EXISTS mail:message:exists 99999  -- returns 0 (definitely does not exist)
```

---

## 10. Cache Warm-Up Strategy

Cache warming reduces the latency impact of cold starts by pre-populating
hot cache keys when a user logs in.

### Trigger: Successful login

After authentication succeeds and before returning the response to the client:

```
1. Load user session → SET session:user:{uid}
2. Load folder list → HSET mail:folder:stats:{uid}
3. Load unread counts → HSET mail:unread:counts:{uid}
4. Load first page of inbox → ZADD mail:message:list:{uid}:{inbox_fid}
```

### Implementation (pseudo-code)

```
async function warmCacheOnLogin(userId) {
    // 1. User session (already set during auth flow)
    // 2. Folder statistics
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

    // 3. Inbox first page (find inbox folder, load 20 newest messages)
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

### Warm-up key inventory

| Priority | Key Pattern | Warm? | Rationale |
|----------|-------------|-------|-----------|
| P0 | `session:user:{uid}` | Yes | Required for every authenticated request |
| P1 | `mail:folder:stats:{uid}` | Yes | Required for sidebar rendering on login |
| P1 | `mail:unread:counts:{uid}` | Yes | Required for badge counts on login |
| P2 | `mail:message:list:{uid}:{inbox}` | Yes | Inbox is the default view, avoid cold-load latency |
| P3 | `mail:message:list:{uid}:{other}` | No | Lazy-load when user navigates to other folders |
| P3 | `mail:message:detail:{mid}` | No | Lazy-load when user opens a specific message |

---

## Summary: TTL Reference Table

| Cache | Key Pattern | TTL | Rationale |
|-------|-------------|-----|-----------|
| Mail list | `mail:message:list:{uid}:{fid}` | 30 min | Balances freshness with DB offload; invalidated on new mail |
| Unread counts | `mail:unread:counts:{uid}` | 5 min | Must be reasonably fresh for accurate badge display |
| User session | `session:user:{uid}` | 24 h | Aligned with JWT expiration |
| Folder stats | `mail:folder:stats:{uid}` | 10 min | Sidebar info changes less frequently |
| Message detail | `mail:message:detail:{mid}` | 1 h | Message content is immutable once received |
| Login rate limit | `ratelimit:login:{ip}` | 15 min (window) | Sliding window for brute-force protection |
| Null sentinel | (any) | 30 s | Short-lived to allow actual creation to supersede quickly |
