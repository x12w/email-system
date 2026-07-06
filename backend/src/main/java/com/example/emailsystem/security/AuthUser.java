package com.example.emailsystem.security;

public record AuthUser(
    Long id,
    String username,
    String displayName
) {
}
