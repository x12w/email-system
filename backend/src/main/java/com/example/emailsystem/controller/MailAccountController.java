package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.*;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.MailAccountService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/mail-accounts")
public class MailAccountController {
    private final MailAccountService mailAccountService;

    public MailAccountController(MailAccountService mailAccountService) {
        this.mailAccountService = mailAccountService;
    }

    @GetMapping
    public ApiResponse<List<MailAccountResponse>> list() {
        return ApiResponse.ok(mailAccountService.listAccounts(SecurityUtils.currentUser().id())
            .stream().map(this::toResponse).collect(Collectors.toList()));
    }

    @PostMapping
    public ApiResponse<MailAccountResponse> create(@Valid @RequestBody MailAccountRequest request) {
        MailAccount account = new MailAccount();
        account.setEmailAddress(request.emailAddress());
        account.setDisplayName(request.displayName());
        account.setSmtpHost(request.smtpHost());
        account.setSmtpPort(request.smtpPort());
        account.setSmtpSsl(request.smtpSsl() ? 1 : 0);
        account.setImapHost(request.imapHost());
        account.setImapPort(request.imapPort());
        account.setImapSsl(request.imapSsl() ? 1 : 0);
        account.setAuthUsername(request.authUsername());
        account.setAuthPasswordEncrypted(request.authPassword());
        MailAccount created = mailAccountService.createAccount(SecurityUtils.currentUser().id(), account);
        return ApiResponse.ok(toResponse(created));
    }

    @PutMapping("/{id}")
    public ApiResponse<MailAccountResponse> update(@PathVariable Long id, @Valid @RequestBody MailAccountRequest request) {
        MailAccount update = new MailAccount();
        update.setEmailAddress(request.emailAddress());
        update.setDisplayName(request.displayName());
        update.setSmtpHost(request.smtpHost());
        update.setSmtpPort(request.smtpPort());
        update.setSmtpSsl(request.smtpSsl() ? 1 : 0);
        update.setImapHost(request.imapHost());
        update.setImapPort(request.imapPort());
        update.setImapSsl(request.imapSsl() ? 1 : 0);
        update.setAuthUsername(request.authUsername());
        update.setAuthPasswordEncrypted(request.authPassword());
        MailAccount updated = mailAccountService.updateAccount(SecurityUtils.currentUser().id(), id, update);
        return ApiResponse.ok(toResponse(updated));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailAccountService.deleteAccount(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }

    @PostMapping("/{id}/test")
    public ApiResponse<Map<String, String>> test(@PathVariable Long id) {
        MailAccount account = mailAccountService.requireAccount(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(Map.of("status", "ok", "message",
            "SMTP " + account.getSmtpHost() + ":" + account.getSmtpPort() + " / IMAP " +
            account.getImapHost() + ":" + account.getImapPort()));
    }

    private MailAccountResponse toResponse(MailAccount a) {
        return new MailAccountResponse(a.getId(), a.getUserId(), a.getEmailAddress(),
            a.getDisplayName(), a.getSmtpHost(), a.getSmtpPort(), a.getSmtpSsl() == 1,
            a.getImapHost(), a.getImapPort(), a.getImapSsl() == 1, a.getAuthUsername(),
            a.getStatus(), a.getLastSyncAt() != null ? a.getLastSyncAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime() : null);
    }
}
