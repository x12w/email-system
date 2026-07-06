package com.example.emailsystem.service;

public interface ImapSyncService {
    void syncAccount(Long userId, Long accountId);
}
