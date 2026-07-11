package com.example.emailsystem.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("user_llm_config")
public class UserLlmConfig {
    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 0=use server default, 1=use custom */
    private Integer useCustom;

    private String baseUrl;
    private String apiKey;
    private String model;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
