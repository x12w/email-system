package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("mail_push_event")
public class MailPushEvent {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long messageId;
    private String eventType;
    private String title;
    private String content;
    private String priority;
    private Integer readFlag;
    private LocalDateTime pushedAt;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
