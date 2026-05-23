package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("mail_intelligence_result")
public class MailIntelligenceResult {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    private Long messageId;
    
    private String spamLabel;
    private BigDecimal spamScore;
    private String priorityLabel;
    private BigDecimal priorityScore;
    private String riskLevel;
    private BigDecimal riskScore;
    
    // 注意：MySQL 的 JSON 类型在 Java 中通常可以用 String 接收
    // 写入时转成 JSON 字符串，或者配合 MyBatis-Plus 的 JacksonTypeHandler 处理
    private String actionJson;
    private String reasonJson;
    
    private String pluginName;
    private String pluginVersion;
    private String status;
    private String errorMessage;
    
    private LocalDateTime analyzedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}