package com.example.emailsystem.intelligence.service.impl;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.UserLlmConfig;
import com.example.emailsystem.intelligence.client.IntelligenceClient;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.service.IntelligenceAnalysisService;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.UserLlmConfigService;
import com.example.emailsystem.service.impl.MailMessageServiceImpl;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class IntelligenceAnalysisServiceImpl implements IntelligenceAnalysisService {

    private static final Logger log = LoggerFactory.getLogger(IntelligenceAnalysisServiceImpl.class);
    private static final int MAX_CACHED_RESULTS = 1000;

    private final IntelligenceClient intelligenceClient;
    private final MailMessageServiceImpl mailMessageService;
    private final UserLlmConfigService userLlmConfigService;
    private final Map<Long, IntelligenceAnalysisResult> results = new ConcurrentHashMap<>();

    public IntelligenceAnalysisServiceImpl(
        IntelligenceClient intelligenceClient,
        MailMessageServiceImpl mailMessageService,
        UserLlmConfigService userLlmConfigService
    ) {
        this.intelligenceClient = intelligenceClient;
        this.mailMessageService = mailMessageService;
        this.userLlmConfigService = userLlmConfigService;
    }

    @Override
    public IntelligenceAnalysisResult analyzeMessage(Long messageId) {
        MailMessage message = mailMessageService.getMessage(SecurityUtils.currentUser().id(), messageId);
        try {
            UserLlmConfig config = userLlmConfigService.getByUserId(SecurityUtils.currentUser().id());
            IntelligenceAnalysisResult result;
            if (config.getUseCustom() != null && config.getUseCustom() == 1
                && config.getBaseUrl() != null && !config.getBaseUrl().isBlank()
                && config.getApiKey() != null && !config.getApiKey().isBlank()
                && config.getModel() != null && !config.getModel().isBlank()) {
                result = intelligenceClient.analyze(message,
                    config.getBaseUrl(), config.getApiKey(), config.getModel());
            } else {
                result = intelligenceClient.analyze(message);
            }
            cacheResult(message.getId(), result);
            return result;
        } catch (Exception exception) {
            throw new BusinessException("INTELLIGENCE_503", "智能分析服务不可用");
        }
    }

    @Override
    public IntelligenceAnalysisResult getMessageResult(Long messageId) {
        IntelligenceAnalysisResult result = results.get(messageId);
        if (result == null) {
            return analyzeMessage(messageId);
        }
        return result;
    }

    private void cacheResult(Long messageId, IntelligenceAnalysisResult result) {
        if (results.size() >= MAX_CACHED_RESULTS) {
            var it = results.keySet().iterator();
            int toRemove = results.size() - MAX_CACHED_RESULTS + 1;
            for (int i = 0; i < toRemove && it.hasNext(); i++) {
                it.next();
                it.remove();
            }
        }
        results.put(messageId, result);
    }
}
