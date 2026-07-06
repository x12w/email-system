package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("mail_intelligence_result")
public class MailIntelligenceResult {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long messageId;
    private String spamLabel;
    private java.math.BigDecimal spamScore;
    private String priorityLabel;
    private java.math.BigDecimal priorityScore;
    private String riskLevel;
    private java.math.BigDecimal riskScore;
    private String actionJson;
    private String reasonJson;
    private String pluginName;
    private String pluginVersion;
    private String status;
    private String errorMessage;
    private LocalDateTime analyzedAt;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
