package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

@Data
@TableName("mail_recipient")
public class MailRecipient {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long messageId;
    private String type;
    private String emailAddress;
    private String displayName;
}
