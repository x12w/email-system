package com.example.emailsystem.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.util.List;

public record SendMessageRequest(
        @NotNull Long accountId,
        @NotEmpty List<@NotBlank String> to,
        List<String> cc,
        List<String> bcc,
        @NotBlank String subject,
        String contentType,
        String content,
        List<Long> attachmentIds
) {}
