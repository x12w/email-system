package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.request.CreateMailAccountRequest;
import com.example.emailsystem.dto.request.UpdateMailAccountRequest;
import com.example.emailsystem.dto.response.MailAccountResponse;
import com.example.emailsystem.service.MailAccountService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/mail-accounts")
public class MailAccountController {

    private final MailAccountService mailAccountService;

    public MailAccountController(MailAccountService mailAccountService) {
        this.mailAccountService = mailAccountService;
    }

    @GetMapping
    public ApiResponse<List<MailAccountResponse>> list(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(mailAccountService.listAccounts(userId));
    }

    @GetMapping("/{id}")
    public ApiResponse<MailAccountResponse> get(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(mailAccountService.getAccount(userId, id));
    }

    @PostMapping
    public ApiResponse<MailAccountResponse> create(Authentication auth, @Valid @RequestBody CreateMailAccountRequest req) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(mailAccountService.createAccount(userId, req));
    }

    @PutMapping("/{id}")
    public ApiResponse<MailAccountResponse> update(Authentication auth, @PathVariable Long id, @Valid @RequestBody UpdateMailAccountRequest req) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(mailAccountService.updateAccount(userId, id, req));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        mailAccountService.deleteAccount(userId, id);
        return ApiResponse.ok(null);
    }

    @PostMapping("/{id}/test")
    public ApiResponse<Void> test(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        mailAccountService.testConnection(userId, id);
        return ApiResponse.ok(null);
    }
}
