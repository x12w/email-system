package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.entity.UserLlmConfig;
import com.example.emailsystem.mapper.UserLlmConfigMapper;
import java.time.LocalDateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class UserLlmConfigService {
    private static final Logger log = LoggerFactory.getLogger(UserLlmConfigService.class);

    private final UserLlmConfigMapper mapper;

    public UserLlmConfigService(UserLlmConfigMapper mapper) {
        this.mapper = mapper;
    }

    /**
     * Get user's LLM config, or a safe default if none saved.
     */
    public UserLlmConfig getByUserId(Long userId) {
        UserLlmConfig config = mapper.selectOne(
            new QueryWrapper<UserLlmConfig>().eq("user_id", userId));
        if (config == null) {
            config = new UserLlmConfig();
            config.setUserId(userId);
            config.setUseCustom(0);
        }
        return config;
    }

    /**
     * Save or update user's LLM config.
     * apiKey is stored as-is (encryption could be added later).
     */
    public UserLlmConfig save(Long userId, String baseUrl, String apiKey, String model, boolean useCustom) {
        try {
            UserLlmConfig existing = mapper.selectOne(
                new QueryWrapper<UserLlmConfig>().eq("user_id", userId));
            if (existing == null) {
                existing = new UserLlmConfig();
                existing.setUserId(userId);
                existing.setCreatedAt(LocalDateTime.now());
                existing.setUpdatedAt(LocalDateTime.now());
                existing.setUseCustom(useCustom ? 1 : 0);
                existing.setBaseUrl(baseUrl);
                existing.setApiKey(apiKey);
                existing.setModel(model);
                mapper.insert(existing);
                log.info("Created LLM config for user {}: useCustom={}, model={}", userId, useCustom, model);
            } else {
                existing.setUseCustom(useCustom ? 1 : 0);
                existing.setBaseUrl(baseUrl);
                existing.setApiKey(apiKey);
                existing.setModel(model);
                existing.setUpdatedAt(LocalDateTime.now());
                mapper.updateById(existing);
                log.info("Updated LLM config for user {}: useCustom={}, model={}", userId, useCustom, model);
            }
            return existing;
        } catch (Exception e) {
            log.error("Failed to save LLM config for user {}: {}", userId, e.getMessage(), e);
            throw e;
        }
    }
}
