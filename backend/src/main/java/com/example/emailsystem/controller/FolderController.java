package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.FolderResponse;
import com.example.emailsystem.entity.MailFolder;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.MailFolderService;
import com.example.emailsystem.service.MailSyncService;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/folders")
public class FolderController {
    private final MailFolderService mailFolderService;
    private final MailSyncService mailSyncService;

    public FolderController(MailFolderService mailFolderService, MailSyncService mailSyncService) {
        this.mailFolderService = mailFolderService;
        this.mailSyncService = mailSyncService;
    }

    @GetMapping
    public ApiResponse<List<FolderResponse>> list() {
        return ApiResponse.ok(mailFolderService.listFolders(SecurityUtils.currentUser().id())
            .stream().map(this::toResponse).collect(Collectors.toList()));
    }

    @PostMapping("/sync")
    public ApiResponse<Map<String, String>> sync() {
        mailSyncService.syncUserAccounts(SecurityUtils.currentUser().id());
        return ApiResponse.ok(Map.of("status", "queued"));
    }

    private FolderResponse toResponse(MailFolder f) {
        return new FolderResponse(f.getId(), f.getAccountId(), f.getName(),
            f.getRemoteName(), f.getType(), f.getUnreadCount(), f.getTotalCount());
    }
}
