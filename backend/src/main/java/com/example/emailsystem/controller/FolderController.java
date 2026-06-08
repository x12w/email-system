package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.FolderResponse;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/folders")
public class FolderController {
    private final DemoMailboxService mailboxService;

    public FolderController(DemoMailboxService mailboxService) {
        this.mailboxService = mailboxService;
    }

    @GetMapping
    public ApiResponse<List<FolderResponse>> list() {
        return ApiResponse.ok(mailboxService.listFolders(SecurityUtils.currentUser().id()));
    }

    @PostMapping("/sync")
    public ApiResponse<Map<String, String>> sync() {
        return ApiResponse.ok(Map.of("status", "queued"));
    }
}
