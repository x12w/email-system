package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("mail_message")
public class MailMessage {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long accountId;
    private Long folderId;
    private String messageUid;
    private String messageId;
    private String fromAddress;
    private String fromName;
    private String subject;
    private String contentType;
    private String content;
    private String preview;
    private LocalDateTime sentAt;
    private LocalDateTime receivedAt;
    private Integer readFlag;
    private Integer starFlag;
    private Integer draftFlag;
    private Integer deletedFlag;
    private Integer attachmentCount;
    private String headers;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
