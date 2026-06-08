package com.example.emailsystem.intelligence.service.impl;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.dto.AppDtos.MessageDetail;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.example.emailsystem.intelligence.plugin.IntelligencePluginClient;
import com.example.emailsystem.intelligence.service.IntelligenceAnalysisService;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.service.DemoMailboxService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class IntelligenceAnalysisServiceImpl implements IntelligenceAnalysisService {
    private final IntelligencePluginClient pluginClient;
    private final DemoMailboxService mailboxService;
    private final ObjectMapper objectMapper;
    private final String pluginName;
    private final Map<Long, IntelligenceAnalysisResult> results = new ConcurrentHashMap<>();

    public IntelligenceAnalysisServiceImpl(
        IntelligencePluginClient pluginClient,
        DemoMailboxService mailboxService,
        ObjectMapper objectMapper,
        @Value("${intelligence.plugin.name}") String pluginName
    ) {
        this.pluginClient = pluginClient;
        this.mailboxService = mailboxService;
        this.objectMapper = objectMapper;
        this.pluginName = pluginName;
    }

    @Override
    public IntelligenceAnalysisResult analyzeMessage(Long messageId) {
        MessageDetail message = mailboxService.getMessage(SecurityUtils.currentUser().id(), messageId);
        try {
            String requestJson = objectMapper.writeValueAsString(Map.of(
                "requestId", "message-" + message.id(),
                "messageId", message.id(),
                "from", message.fromAddress(),
                "to", message.to(),
                "subject", message.subject(),
                "plainText", message.preview(),
                "html", message.content(),
                "links", extractLinks(message.content()),
                "attachments", List.of(),
                "locale", "zh-CN"
            ));
            JsonNode root = objectMapper.readTree(pluginClient.analyzeEmailJson(requestJson));
            JsonNode spam = root.path("spam");
            JsonNode priority = root.path("priority");
            JsonNode risk = root.path("risk");
            List<ThreatIndicator> threats = new ArrayList<>();
            for (JsonNode indicator : risk.path("indicators")) {
                threats.add(new ThreatIndicator(
                    indicator.path("type").asText(),
                    indicator.path("value").asText(),
                    indicator.path("riskLevel").asText(),
                    indicator.path("reason").asText()
                ));
            }
            IntelligenceAnalysisResult result = new IntelligenceAnalysisResult(
                message.id(),
                spam.path("label").asText("unknown"),
                BigDecimal.valueOf(spam.path("score").asDouble(0)),
                priority.path("label").asText("normal"),
                BigDecimal.valueOf(priority.path("score").asDouble(0)),
                risk.path("level").asText("none"),
                BigDecimal.valueOf(risk.path("score").asDouble(0)),
                pluginName,
                root.path("pluginVersion").asText("0.1.0"),
                OffsetDateTime.now(),
                threats
            );
            results.put(message.id(), result);
            mailboxService.applyIntelligence(message.id(), result.spamLabel(), result.priorityLabel(), result.riskLevel());
            return result;
        } catch (Exception exception) {
            throw new BusinessException("INTELLIGENCE_503", "智能分析插件不可用");
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

    private List<String> extractLinks(String content) {
        List<String> links = new ArrayList<>();
        for (String token : content.split("\\s+")) {
            String cleaned = token.replaceAll("[<>\"')]", "");
            if (cleaned.startsWith("http://") || cleaned.startsWith("https://")) {
                links.add(cleaned);
            }
        }
        return links;
    }
}
