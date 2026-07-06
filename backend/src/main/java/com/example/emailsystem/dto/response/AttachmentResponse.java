package com.example.emailsystem.dto.response;

import com.example.emailsystem.entity.MailAttachment;

import java.time.LocalDateTime;

public record AttachmentResponse(
        Long id,
        String originalName,
        String contentType,
        Long sizeBytes,
        LocalDateTime createdAt
) {
    public static AttachmentResponse from(MailAttachment att) {
        return new AttachmentResponse(
                att.getId(), att.getOriginalName(), att.getContentType(),
                att.getSizeBytes(), att.getCreatedAt()
        );
    }
}
