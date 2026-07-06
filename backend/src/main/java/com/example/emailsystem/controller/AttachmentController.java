package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.AttachmentResponse;
import com.example.emailsystem.entity.MailAttachment;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.AttachmentService;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/attachments")
public class AttachmentController {
    private final AttachmentService attachmentService;

    public AttachmentController(AttachmentService attachmentService) {
        this.attachmentService = attachmentService;
    }

    @PostMapping
    public ApiResponse<AttachmentResponse> upload(@RequestPart("file") MultipartFile file) {
        MailAttachment a = attachmentService.upload(SecurityUtils.currentUser().id(), file);
        return ApiResponse.ok(toResponse(a));
    }

    @GetMapping("/{id}/download")
    public ResponseEntity<byte[]> download(@PathVariable Long id) {
        MailAttachment a = attachmentService.getAttachment(id);
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment()
                .filename(a.getOriginalName()).build().toString())
            .body(attachmentService.download(id));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        attachmentService.delete(id);
        return ApiResponse.ok(null);
    }

    private AttachmentResponse toResponse(MailAttachment a) {
        return new AttachmentResponse(a.getId(), a.getOriginalName(), a.getContentType(),
            a.getSizeBytes(), a.getStorageType(), "/api/attachments/" + a.getId() + "/download");
    }
}
