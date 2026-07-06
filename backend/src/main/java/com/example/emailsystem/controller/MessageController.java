package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.request.SaveDraftRequest;
import com.example.emailsystem.dto.request.SendMessageRequest;
import com.example.emailsystem.dto.response.MessageResponse;
import com.example.emailsystem.dto.response.PageResult;
import com.example.emailsystem.service.MailSendService;
import com.example.emailsystem.service.MessageQueryService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/messages")
public class MessageController {

    private final MailSendService mailSendService;
    private final MessageQueryService messageQueryService;

    public MessageController(MailSendService mailSendService, MessageQueryService messageQueryService) {
        this.mailSendService = mailSendService;
        this.messageQueryService = messageQueryService;
    }

    @GetMapping
    public ApiResponse<PageResult<MessageResponse>> list(
            Authentication auth,
            @RequestParam(required = false) Long folderId,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Boolean read,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size
    ) {
        Long userId = (Long) auth.getPrincipal();
        var records = messageQueryService.listMessages(userId, folderId, keyword, read, page, size);
        long total = messageQueryService.countTotal(userId, folderId, keyword, read);
        return ApiResponse.ok(PageResult.of(records, page, size, total));
    }

    @GetMapping("/{id}")
    public ApiResponse<MessageResponse> detail(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(messageQueryService.getMessage(userId, id));
    }

    @PostMapping("/send")
    public ApiResponse<MessageResponse> send(Authentication auth, @Valid @RequestBody SendMessageRequest req) {
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(mailSendService.send(userId, req));
    }

    @PostMapping("/drafts")
    public ApiResponse<Void> saveDraft(Authentication auth, @Valid @RequestBody SaveDraftRequest req) {
        // Draft saving will be implemented with full message editing support
        Long userId = (Long) auth.getPrincipal();
        return ApiResponse.ok(null);
    }

    @PutMapping("/{id}/read")
    public ApiResponse<Void> markRead(Authentication auth, @PathVariable Long id, @RequestParam(defaultValue = "true") boolean read) {
        Long userId = (Long) auth.getPrincipal();
        messageQueryService.markRead(userId, id, read);
        return ApiResponse.ok(null);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        messageQueryService.deleteMessage(userId, id);
        return ApiResponse.ok(null);
    }
}
