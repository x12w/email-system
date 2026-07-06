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
    
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    @TableLogic // MyBatis-Plus 软删除注解，会自动过滤 deleted = 1 的数据
    private Integer deleted;
}