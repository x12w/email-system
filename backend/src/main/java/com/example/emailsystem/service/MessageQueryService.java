package com.example.emailsystem.service;

import com.example.emailsystem.dto.response.MessageResponse;

import java.util.List;

public interface MessageQueryService {
    List<MessageResponse> listMessages(Long userId, Long folderId, String keyword, Boolean read, int page, int size);
    MessageResponse getMessage(Long userId, Long id);
    void markRead(Long userId, Long id, boolean read);
    void deleteMessage(Long userId, Long id);
    long countTotal(Long userId, Long folderId, String keyword, Boolean read);
}
