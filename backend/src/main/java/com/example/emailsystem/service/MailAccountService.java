package com.example.emailsystem.service;

import com.example.emailsystem.dto.request.CreateMailAccountRequest;
import com.example.emailsystem.dto.request.UpdateMailAccountRequest;
import com.example.emailsystem.dto.response.MailAccountResponse;

import java.util.List;

public interface MailAccountService {
    List<MailAccountResponse> listAccounts(Long userId);
    MailAccountResponse getAccount(Long userId, Long id);
    MailAccountResponse createAccount(Long userId, CreateMailAccountRequest req);
    MailAccountResponse updateAccount(Long userId, Long id, UpdateMailAccountRequest req);
    void deleteAccount(Long userId, Long id);
    void testConnection(Long userId, Long id);
}
