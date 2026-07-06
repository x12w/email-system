package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("mail_threat_indicator")
public class MailThreatIndicator {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long messageId;
    private Long intelligenceResultId;
    private String type;
    private String value;
    private String riskLevel;
    private String reason;
    private String ruleId;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
