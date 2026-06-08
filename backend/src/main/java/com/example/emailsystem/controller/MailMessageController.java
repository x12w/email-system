package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.common.PageResult;
import com.example.emailsystem.dto.AppDtos.MessageDetail;
import com.example.emailsystem.dto.AppDtos.MessageSummary;
import com.example.emailsystem.dto.AppDtos.ReadRequest;
import com.example.emailsystem.dto.AppDtos.SendMessageRequest;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/messages")
public class MailMessageController {
    private final DemoMailboxService mailboxService;

    public MailMessageController(DemoMailboxService mailboxService) {
        this.mailboxService = mailboxService;
    }

    @GetMapping
    public ApiResponse<PageResult<MessageSummary>> list(
        @RequestParam(required = false) Long folderId,
        @RequestParam(required = false) String keyword,
        @RequestParam(required = false) Boolean read,
        @RequestParam(required = false) String spamLabel,
        @RequestParam(required = false) String priorityLabel,
        @RequestParam(required = false) String riskLevel,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        return ApiResponse.ok(mailboxService.listMessages(
            SecurityUtils.currentUser().id(), folderId, keyword, read, spamLabel, priorityLabel, riskLevel, page, size
        ));
    }

    @GetMapping("/{id}")
    public ApiResponse<MessageDetail> detail(@PathVariable Long id) {
        return ApiResponse.ok(mailboxService.getMessage(SecurityUtils.currentUser().id(), id));
    }

    @PostMapping("/send")
    public ApiResponse<MessageDetail> send(@Valid @RequestBody SendMessageRequest request) {
        return ApiResponse.ok(mailboxService.sendMessage(SecurityUtils.currentUser().id(), request, false));
    }

    @PostMapping("/drafts")
    public ApiResponse<MessageDetail> draft(@Valid @RequestBody SendMessageRequest request) {
        return ApiResponse.ok(mailboxService.sendMessage(SecurityUtils.currentUser().id(), request, true));
    }

    @PutMapping("/{id}/read")
    public ApiResponse<MessageDetail> markRead(@PathVariable Long id, @RequestBody ReadRequest request) {
        return ApiResponse.ok(mailboxService.markRead(SecurityUtils.currentUser().id(), id, request));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailboxService.deleteMessage(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }
}
