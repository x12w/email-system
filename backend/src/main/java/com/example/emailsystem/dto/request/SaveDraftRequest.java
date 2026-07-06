package com.example.emailsystem.dto.request;

import jakarta.validation.constraints.NotNull;

import java.util.List;

public record SaveDraftRequest(
        @NotNull Long accountId,
        List<String> to,
        List<String> cc,
        List<String> bcc,
        String subject,
        String contentType,
        String content,
        List<Long> attachmentIds
) {}
