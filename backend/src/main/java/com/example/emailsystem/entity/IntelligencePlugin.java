package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("intelligence_plugin")
public class IntelligencePlugin {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String version;
    private String runtime;
    private String artifactPath;
    private String checksum;
    private Integer enabled;
    private Integer timeoutMs;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
