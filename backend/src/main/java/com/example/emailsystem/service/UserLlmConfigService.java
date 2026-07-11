package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.entity.UserLlmConfig;
import com.example.emailsystem.mapper.UserLlmConfigMapper;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;

@Service
public class UserLlmConfigService {

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
        } else {
            existing.setUseCustom(useCustom ? 1 : 0);
            existing.setBaseUrl(baseUrl);
            existing.setApiKey(apiKey);
            existing.setModel(model);
            existing.setUpdatedAt(LocalDateTime.now());
            mapper.updateById(existing);
        }
        return existing;
    }
}
