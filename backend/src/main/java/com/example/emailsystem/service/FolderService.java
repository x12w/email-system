package com.example.emailsystem.service;

import com.example.emailsystem.dto.response.FolderResponse;

import java.util.List;

public interface FolderService {
    List<FolderResponse> listFolders(Long userId);
    void syncRemoteFolders(Long userId);
}
