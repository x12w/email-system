package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.service.ImapSyncService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/sync")
public class SyncController {

    private final ImapSyncService imapSyncService;

    public SyncController(ImapSyncService imapSyncService) {
        this.imapSyncService = imapSyncService;
    }

    @PostMapping("/imap/{accountId}")
    public ApiResponse<Void> syncImap(Authentication auth, @PathVariable Long accountId) {
        Long userId = (Long) auth.getPrincipal();
        imapSyncService.syncAccount(userId, accountId);
        return ApiResponse.ok(null);
    }
}
