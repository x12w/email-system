package com.example.emailsystem.dto;

public record LoginResponse(
        String accessToken,
        long expiresIn,
        UserInfo user
) {
    public record UserInfo(Long id, String username, String displayName) {}
}
