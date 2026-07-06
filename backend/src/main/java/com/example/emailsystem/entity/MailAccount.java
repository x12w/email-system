package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("mail_account")
public class MailAccount {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private String emailAddress;
    private String displayName;
    private String smtpHost;
    private Integer smtpPort;
    private Integer smtpSsl;
    private String imapHost;
    private Integer imapPort;
    private Integer imapSsl;
    private String authUsername;
    private String authPasswordEncrypted;
    private Integer status;
    private LocalDateTime lastSyncAt;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
