package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.response.FolderResponse;
import com.example.emailsystem.service.FolderService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/folders")
public class FolderController {

    private final FolderService folderService;

    public FolderController(FolderService folderService) {
        this.folderService = folderService;
    }

    @GetMapping
    public ApiResponse<List<FolderResponse>> list(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(folderService.listFolders(userId));
    }

    @PostMapping("/sync")
    public ApiResponse<Void> sync(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        folderService.syncRemoteFolders(userId);
        return ApiResponse.ok(null);
    }
}
