package com.example.emailsystem.dto.response;

import com.example.emailsystem.entity.MailMessage;

import java.time.LocalDateTime;

public record MessageResponse(
        Long id,
        Long accountId,
        Long folderId,
        String fromAddress,
        String fromName,
        String subject,
        String contentType,
        String content,
        String preview,
        LocalDateTime sentAt,
        LocalDateTime receivedAt,
        Integer readFlag,
        Integer starFlag,
        Integer draftFlag,
        Integer attachmentCount,
        LocalDateTime createdAt
) {
    public static MessageResponse from(MailMessage msg) {
        return new MessageResponse(
                msg.getId(), msg.getAccountId(), msg.getFolderId(),
                msg.getFromAddress(), msg.getFromName(),
                msg.getSubject(), msg.getContentType(), msg.getContent(), msg.getPreview(),
                msg.getSentAt(), msg.getReceivedAt(),
                msg.getReadFlag(), msg.getStarFlag(), msg.getDraftFlag(),
                msg.getAttachmentCount(), msg.getCreatedAt()
        );
    }
}
