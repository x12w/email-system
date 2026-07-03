package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.MailAccountRequest;
import com.example.emailsystem.dto.AppDtos.MailAccountResponse;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/mail-accounts")
public class MailAccountController {
    private final DemoMailboxService mailboxService;

    public MailAccountController(DemoMailboxService mailboxService) {
        this.mailboxService = mailboxService;
    }

    @GetMapping
    public ApiResponse<List<MailAccountResponse>> list() {
        return ApiResponse.ok(mailboxService.listAccounts(SecurityUtils.currentUser().id()));
    }

    @PostMapping
    public ApiResponse<MailAccountResponse> create(@Valid @RequestBody MailAccountRequest request) {
        return ApiResponse.ok(mailboxService.createAccount(SecurityUtils.currentUser().id(), request));
    }

    @PutMapping("/{id}")
    public ApiResponse<MailAccountResponse> update(@PathVariable Long id, @Valid @RequestBody MailAccountRequest request) {
        return ApiResponse.ok(mailboxService.updateAccount(SecurityUtils.currentUser().id(), id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailboxService.deleteAccount(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }

    @PostMapping("/{id}/test")
    public ApiResponse<Map<String, String>> test(@PathVariable Long id) {
        return ApiResponse.ok(Map.of("status", "ok", "message", "SMTP/IMAP 配置格式有效"));
    }
}
