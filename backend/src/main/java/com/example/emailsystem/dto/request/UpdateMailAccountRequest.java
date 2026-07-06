package com.example.emailsystem.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record UpdateMailAccountRequest(
        @NotBlank String emailAddress,
        String displayName,
        @NotBlank String smtpHost,
        @NotNull Integer smtpPort,
        Integer smtpSsl,
        @NotBlank String imapHost,
        @NotNull Integer imapPort,
        Integer imapSsl,
        @NotBlank String authUsername,
        String authPassword
) {}
