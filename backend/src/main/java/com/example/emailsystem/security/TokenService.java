package com.example.emailsystem.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class TokenService {
    private static final int MIN_SECRET_LENGTH = 16;
    private final String secret;
    private final long expireSeconds;
    private final ObjectMapper objectMapper;

    public TokenService(
        @Value("${security.jwt.secret}") String secret,
        @Value("${security.jwt.expire-seconds}") long expireSeconds,
        ObjectMapper objectMapper
    ) {
        this.secret = secret;
        this.expireSeconds = expireSeconds;
        this.objectMapper = objectMapper;
    }

    @PostConstruct
    void validateSecret() {
        if (secret == null || secret.isBlank() || secret.contains("replace-with") || secret.length() < MIN_SECRET_LENGTH) {
            throw new IllegalStateException(
                "JWT secret is missing, too short (< " + MIN_SECRET_LENGTH + " chars), or uses a placeholder value. " +
                "Set the JWT_SECRET environment variable to a secure random string."
            );
        }
    }

    public String createAccessToken(AuthUser user) {
        return createToken(user, expireSeconds);
    }

    public String createRefreshToken(AuthUser user) {
        return createToken(user, expireSeconds * 24);
    }

    public long expireSeconds() {
        return expireSeconds;
    }

    public AuthUser parse(String token) {
        try {
            String[] parts = token.split("\\.");
            if (parts.length != 2 || !signature(parts[0]).equals(parts[1])) {
                return null;
            }
            Payload payload = objectMapper.readValue(
                Base64.getUrlDecoder().decode(parts[0]),
                Payload.class
            );
            if (payload.exp() < Instant.now().getEpochSecond()) {
                return null;
            }
            return new AuthUser(payload.id(), payload.username(), payload.displayName());
        } catch (Exception exception) {
            return null;
        }
    }

    private String createToken(AuthUser user, long ttlSeconds) {
        try {
            Payload payload = new Payload(
                user.id(),
                user.username(),
                user.displayName(),
                Instant.now().plusSeconds(ttlSeconds).getEpochSecond()
            );
            String body = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(objectMapper.writeValueAsBytes(payload));
            return body + "." + signature(body);
        } catch (Exception exception) {
            throw new IllegalStateException("Cannot create token", exception);
        }
    }

    private String signature(String body) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(body.getBytes(StandardCharsets.UTF_8)));
    }

    private record Payload(Long id, String username, String displayName, long exp) {
    }
}
