package com.example.emailsystem.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.OffsetDateTime;
import java.util.List;

public final class AppDtos {
    private AppDtos() {
    }

    public record UserInfo(Long id, String username, String displayName) {
    }

    public record LoginRequest(@NotBlank String username, @NotBlank String password) {
    }

    public record LoginResponse(String accessToken, String refreshToken, long expiresIn, UserInfo user) {
    }

    public record MailAccountRequest(
        @NotBlank @Email String emailAddress,
        String displayName,
        @NotBlank String smtpHost,
        int smtpPort,
        boolean smtpSsl,
        String imapHost,
        Integer imapPort,
        boolean imapSsl,
        @NotBlank String authUsername,
        @NotBlank String authPassword
    ) {
    }

    public record MailAccountResponse(
        Long id,
        Long userId,
        String emailAddress,
        String displayName,
        String smtpHost,
        int smtpPort,
        boolean smtpSsl,
        String imapHost,
        Integer imapPort,
        boolean imapSsl,
        String authUsername,
        int status,
        OffsetDateTime lastSyncAt
    ) {
    }

    public record FolderResponse(
        Long id,
        Long accountId,
        String name,
        String remoteName,
        String type,
        int unreadCount,
        int totalCount
    ) {
    }

    public record MessageSummary(
        Long id,
        Long accountId,
        Long folderId,
        String fromAddress,
        String fromName,
        String subject,
        String preview,
        OffsetDateTime receivedAt,
        boolean read,
        boolean starred,
        boolean draft,
        int attachmentCount,
        String spamLabel,
        String priorityLabel,
        String riskLevel
    ) {
    }

    public record MessageDetail(
        Long id,
        Long accountId,
        Long folderId,
        String fromAddress,
        String fromName,
        List<String> to,
        List<String> cc,
        List<String> bcc,
        String subject,
        String contentType,
        String content,
        String preview,
        OffsetDateTime sentAt,
        OffsetDateTime receivedAt,
        boolean read,
        boolean starred,
        boolean draft,
        int attachmentCount,
        String spamLabel,
        String priorityLabel,
        String riskLevel
    ) {
    }

    public record SendMessageRequest(
        @NotNull Long accountId,
        List<@Email String> to,
        List<@Email String> cc,
        List<@Email String> bcc,
        @NotBlank String subject,
        String contentType,
        String content,
        List<Long> attachmentIds
    ) {
    }

    public record ReadRequest(boolean read) {
    }

    public record ContactRequest(
        @NotBlank String name,
        @NotBlank @Email String emailAddress,
        String phone,
        String remark
    ) {
    }

    public record ContactResponse(
        Long id,
        String name,
        String emailAddress,
        String phone,
        String remark
    ) {
    }

    public record AttachmentResponse(
        Long id,
        String originalName,
        String contentType,
        long sizeBytes,
        String storageType,
        String downloadUrl
    ) {
    }

    public record PushEventResponse(
        Long id,
        Long messageId,
        String eventType,
        String title,
        String content,
        String priority,
        boolean read,
        OffsetDateTime pushedAt
    ) {
    }

    public record PluginStatusResponse(
        String name,
        String version,
        String runtime,
        boolean enabled,
        int timeoutMs,
        String status
    ) {
    }
}
