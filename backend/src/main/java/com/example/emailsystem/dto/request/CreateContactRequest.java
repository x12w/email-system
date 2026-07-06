package com.example.emailsystem.dto.request;

import jakarta.validation.constraints.NotBlank;

public record CreateContactRequest(
        @NotBlank String name,
        @NotBlank String emailAddress,
        String phone,
        String remark
) {}
