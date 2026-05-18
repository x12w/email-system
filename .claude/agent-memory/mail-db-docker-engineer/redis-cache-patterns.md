---
name: redis-cache-patterns
description: Redis cache key conventions, TTL values, data structure choices, and invalidation strategies for the email system
metadata:
  type: reference
---

## Key Naming Convention

Pattern: `mail:{module}:{entity}:{identifier}`

For sessions: `session:user:{user_id}`
For rate limiting: `ratelimit:login:{ip_address}`

## Data Structure Choices

| Use Case | Redis Type | Why |
|----------|-----------|-----|
| Mail list (per folder) | Sorted Set | Natural pagination by received_at, ZREVRANGEBYSCORE for newest-first |
| Unread counts | Hash | Per-user, field=folder_id, atomic HINCRBY for increment/decrement |
| Folder statistics | Hash | Per-user, field=folder_id, value=JSON blob |
| Message detail | String (JSON) | Single-key lookup, full message data |
| User session | String (JSON) | Single-key lookup, contains user info + roles + permissions |
| Login rate limiting | Sorted Set | Sliding window, score=timestamp, ZREMRANGEBYSCORE to evict |

## TTL Values

- Mail list: 30 min
- Unread counts: 5 min
- Folder stats: 10 min
- Message detail: 1 hour
- User session: 24 hours (aligned with JWT)
- Rate limit window: 15 min
- Null sentinel: 30 seconds

## Invalidation Strategy: Cache-Aside

1. Write path: Update DB → DELETE affected cache keys
2. Read path: Check cache → on MISS, load from DB → populate cache
3. Null sentinel ("NULL" with 30s TTL) prevents cache penetration for non-existent resources

## Cache Warm-Up (on login)

Preload in priority order: P0 session → P1 folder stats + unread counts → P2 inbox first page
Other folders and message details are lazy-loaded on first access.
