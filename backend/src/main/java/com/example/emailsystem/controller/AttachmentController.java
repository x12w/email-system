package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.AttachmentResponse;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/attachments")
public class AttachmentController {
    private final DemoMailboxService mailboxService;

    public AttachmentController(DemoMailboxService mailboxService) {
        this.mailboxService = mailboxService;
    }

    @PostMapping
    public ApiResponse<AttachmentResponse> upload(@RequestPart("file") MultipartFile file) {
        return ApiResponse.ok(mailboxService.uploadAttachment(SecurityUtils.currentUser().id(), file));
    }

    @GetMapping("/{id}/download")
    public ResponseEntity<byte[]> download(@PathVariable Long id) {
        AttachmentResponse attachment = mailboxService.getAttachment(id);
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment()
                .filename(attachment.originalName())
                .build()
                .toString())
            .body(mailboxService.downloadAttachment(id));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        mailboxService.deleteAttachment(id);
        return ApiResponse.ok(null);
    }
}
