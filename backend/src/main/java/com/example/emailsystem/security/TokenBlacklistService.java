package com.example.emailsystem.security;

import java.time.Duration;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

/**
 * Redis-backed token blacklist so that logout and token revocation actually work.
 * Blacklisted tokens are stored with a TTL matching their remaining validity,
 * so entries auto-expire when the original token would have expired anyway.
 */
@Service
public class TokenBlacklistService {
    private static final Logger log = LoggerFactory.getLogger(TokenBlacklistService.class);
    private static final String BLACKLIST_PREFIX = "token:blacklist:";

    private final StringRedisTemplate redisTemplate;
    private final TokenService tokenService;

    public TokenBlacklistService(StringRedisTemplate redisTemplate, TokenService tokenService) {
        this.redisTemplate = redisTemplate;
        this.tokenService = tokenService;
    }

    /**
     * Add a token to the blacklist. The entry expires when the token would expire.
     */
    public void blacklist(String token) {
        // Store with TTL = token's remaining lifetime + 60s buffer
        long ttlSeconds = tokenService.expireSeconds() + 60;
        redisTemplate.opsForValue().set(BLACKLIST_PREFIX + token, "1", Duration.ofSeconds(ttlSeconds));
        log.debug("Token blacklisted, expires in {}s", ttlSeconds);
    }

    /**
     * Check whether a token has been blacklisted (i.e., user logged out).
     */
    public boolean isBlacklisted(String token) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(BLACKLIST_PREFIX + token));
    }
}
