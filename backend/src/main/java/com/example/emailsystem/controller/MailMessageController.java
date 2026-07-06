package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.common.PageResult;
import com.example.emailsystem.dto.AppDtos.*;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.MailAccountService;
import com.example.emailsystem.service.MailSenderService;
import com.example.emailsystem.service.MailSyncService;
import com.example.emailsystem.service.impl.MailMessageServiceImpl;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/messages")
public class MailMessageController {
    private final MailMessageServiceImpl mailMessageService;
    private final MailSenderService mailSenderService;
    private final MailAccountService mailAccountService;
    private final MailSyncService mailSyncService;

    public MailMessageController(MailMessageServiceImpl mailMessageService,
                                  MailSenderService mailSenderService,
                                  MailAccountService mailAccountService,
                                  MailSyncService mailSyncService) {
        this.mailMessageService = mailMessageService;
        this.mailSenderService = mailSenderService;
        this.mailAccountService = mailAccountService;
        this.mailSyncService = mailSyncService;
    }

    @GetMapping
    public ApiResponse<PageResult<MessageSummary>> list(
        @RequestParam(required = false) Long folderId,
        @RequestParam(required = false) String keyword,
        @RequestParam(required = false) Boolean read,
        @RequestParam(defaultValue = "1") int page,
        @RequestParam(defaultValue = "20") int size
    ) {
        Long userId = SecurityUtils.currentUser().id();
        List<Long> accountIds = mailAccountService.listAccounts(userId).stream()
            .map(MailAccount::getId).collect(Collectors.toList());
        PageResult<MailMessage> result = mailMessageService.listMessages(
            userId, folderId, keyword, read, accountIds, page, size);

        List<MessageSummary> records = result.records().stream()
            .map(m -> new MessageSummary(
                m.getId(), m.getAccountId(), m.getFolderId(),
                m.getFromAddress(), m.getFromName(), m.getSubject(), m.getPreview(),
                m.getReceivedAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime(),
                m.getReadFlag() == 1, m.getStarFlag() == 1, m.getDraftFlag() == 1,
                m.getAttachmentCount(), "normal", "normal", "none"))
            .collect(Collectors.toList());

        return ApiResponse.ok(new PageResult<>(records, result.page(), result.size(), result.total()));
    }

    @GetMapping("/{id}")
    public ApiResponse<MessageDetail> detail(@PathVariable Long id) {
        Long userId = SecurityUtils.currentUser().id();
        MailMessage m = mailMessageService.getMessage(userId, id);
        List<MailRecipient> recipients = mailMessageService.getRecipients(id);

        List<String> to = filterByType(recipients, "to");
        List<String> cc = filterByType(recipients, "cc");
        List<String> bcc = filterByType(recipients, "bcc");

        return ApiResponse.ok(new MessageDetail(
            m.getId(), m.getAccountId(), m.getFolderId(),
            m.getFromAddress(), m.getFromName(), to, cc, bcc,
            m.getSubject(), m.getContentType(), m.getContent(), m.getPreview(),
            m.getSentAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime(),
            m.getReceivedAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime(),
            m.getReadFlag() == 1, m.getStarFlag() == 1, m.getDraftFlag() == 1,
            m.getAttachmentCount(), "normal", "normal", "none"));
    }

    @PostMapping("/send")
    public ApiResponse<MessageDetail> send(@Valid @RequestBody SendMessageRequest request) {
        Long userId = SecurityUtils.currentUser().id();
        MailAccount account = mailAccountService.requireAccount(userId, request.accountId());
        List<String> to = defaultList(request.to());
        List<String> cc = defaultList(request.cc());
        List<String> bcc = defaultList(request.bcc());

        MailMessage message = mailSenderService.send(account, request.subject(),
            request.contentType(), request.content(), to, cc, bcc, request.attachmentIds(), userId);

        return ApiResponse.ok(toDetail(message));
    }

    @PostMapping("/drafts")
    public ApiResponse<MessageDetail> draft(@Valid @RequestBody SendMessageRequest request) {
        Long userId = SecurityUtils.currentUser().id();
        MailAccount account = mailAccountService.requireAccount(userId, request.accountId());
        List<String> to = defaultList(request.to());
        List<String> cc = defaultList(request.cc());
        List<String> bcc = defaultList(request.bcc());

        MailMessage message = mailSenderService.saveDraft(account, request.subject(),
            request.contentType(), request.content(), to, cc, bcc, request.attachmentIds(), userId);

        return ApiResponse.ok(toDetail(message));
    }

    @PutMapping("/{id}/read")
    public ApiResponse<MessageDetail> markRead(@PathVariable Long id, @RequestBody ReadRequest request) {
        Long userId = SecurityUtils.currentUser().id();
        mailMessageService.markRead(userId, id, request.read());
        MailMessage m = mailMessageService.getMessage(userId, id);
        return ApiResponse.ok(toDetail(m));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailMessageService.softDelete(SecurityUtils.currentUser().id(), id);
        return ApiResponse.ok(null);
    }

    @PostMapping("/sync")
    public ApiResponse<java.util.Map<String, String>> sync() {
        mailSyncService.syncUserAccounts(SecurityUtils.currentUser().id());
        return ApiResponse.ok(java.util.Map.of("status", "queued"));
    }

    private MessageDetail toDetail(MailMessage m) {
        return new MessageDetail(
            m.getId(), m.getAccountId(), m.getFolderId(),
            m.getFromAddress(), m.getFromName(), List.of(), List.of(), List.of(),
            m.getSubject(), m.getContentType(), m.getContent(), m.getPreview(),
            m.getSentAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime(),
            m.getReceivedAt().atZone(java.time.ZoneId.systemDefault()).toOffsetDateTime(),
            m.getReadFlag() == 1, m.getStarFlag() == 1, m.getDraftFlag() == 1,
            m.getAttachmentCount(), "normal", "normal", "none");
    }

    private List<String> filterByType(List<MailRecipient> recipients, String type) {
        return recipients.stream()
            .filter(r -> type.equals(r.getType()))
            .map(MailRecipient::getEmailAddress)
            .collect(Collectors.toList());
    }

    private List<String> defaultList(List<String> values) {
        return values == null ? List.of() : values;
    }
}
