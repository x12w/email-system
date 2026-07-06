package com.example.emailsystem.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank(message = "用户名不能为空") @Size(min = 3, max = 64) String username,
        @NotBlank(message = "密码不能为空") @Size(min = 6, max = 128) String password,
        @NotBlank(message = "显示名称不能为空") String displayName
) {}
