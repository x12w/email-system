package com.example.emailsystem.intelligence.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.entity.*;
import com.example.emailsystem.event.MailMessageSyncedEvent;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.example.emailsystem.intelligence.plugin.IntelligencePluginClient;
import com.example.emailsystem.mapper.*;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.event.TransactionalEventListener;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.*;

@Service
public class IntelligenceAnalysisServiceImpl implements IntelligenceAnalysisService {

    private static final Logger log = LoggerFactory.getLogger(IntelligenceAnalysisServiceImpl.class);

    private final MailMessageMapper messageMapper;
    private final MailRecipientMapper recipientMapper;
    private final MailAttachmentMapper attachmentMapper;
    private final MailIntelligenceResultMapper resultMapper;
    private final MailThreatIndicatorMapper threatIndicatorMapper;
    private final MailPushEventMapper pushEventMapper;
    private final IntelligencePluginClient pluginClient;
    private final ObjectMapper objectMapper;

    public IntelligenceAnalysisServiceImpl(MailMessageMapper messageMapper,
                                           MailRecipientMapper recipientMapper,
                                           MailAttachmentMapper attachmentMapper,
                                           MailIntelligenceResultMapper resultMapper,
                                           MailThreatIndicatorMapper threatIndicatorMapper,
                                           MailPushEventMapper pushEventMapper,
                                           IntelligencePluginClient pluginClient,
                                           ObjectMapper objectMapper) {
        this.messageMapper = messageMapper;
        this.recipientMapper = recipientMapper;
        this.attachmentMapper = attachmentMapper;
        this.resultMapper = resultMapper;
        this.threatIndicatorMapper = threatIndicatorMapper;
        this.pushEventMapper = pushEventMapper;
        this.pluginClient = pluginClient;
        this.objectMapper = objectMapper;
    }

    @Override
    @Transactional
    public IntelligenceAnalysisResult analyzeMessage(Long messageId) {
        MailMessage msg = messageMapper.selectById(messageId);
        if (msg == null) throw new IllegalArgumentException("邮件不存在");

        List<MailRecipient> recipients = recipientMapper.selectList(
                new LambdaQueryWrapper<MailRecipient>().eq(MailRecipient::getMessageId, messageId));
        List<MailAttachment> attachments = attachmentMapper.selectList(
                new LambdaQueryWrapper<MailAttachment>().eq(MailAttachment::getMessageId, messageId));

        // Build request payload
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("messageId", messageId);
        payload.put("requestId", UUID.randomUUID().toString());
        payload.put("from", msg.getFromAddress());
        payload.put("fromName", msg.getFromName() != null ? msg.getFromName() : "");
        payload.put("to", recipients.stream().map(MailRecipient::getEmailAddress).toList());
        payload.put("subject", msg.getSubject() != null ? msg.getSubject() : "");
        payload.put("plainText", "");
        payload.put("html", msg.getContent() != null ? msg.getContent() : "");
        payload.put("links", extractLinks(msg.getContent()));
        payload.put("attachments", attachments.stream()
                .map(a -> Map.of("filename", a.getOriginalName(), "size", a.getSizeBytes()))
                .toList());
        payload.put("locale", "zh-CN");

        // Include email headers for header analysis
        if (msg.getHeaders() != null && !msg.getHeaders().isBlank()) {
            try {
                @SuppressWarnings("unchecked")
                Map<String, Object> headers = objectMapper.readValue(msg.getHeaders(), Map.class);
                payload.put("headers", headers);
            } catch (Exception e) {
                log.warn("Failed to parse headers JSON for message {}: {}", messageId, e.getMessage());
            }
        }

        try {
            String requestJson = objectMapper.writeValueAsString(payload);
            String responseJson = pluginClient.analyzeEmailJson(requestJson);

            Map<String, Object> result = objectMapper.readValue(responseJson,
                    new TypeReference<Map<String, Object>>() {});

            // Save intelligence result
            MailIntelligenceResult entity = new MailIntelligenceResult();
            entity.setUserId(msg.getUserId());
            entity.setMessageId(messageId);
            entity.setSpamLabel((String) getNested(result, "spam", "label"));
            entity.setSpamScore(bigDecimalOrZero(getNested(result, "spam", "score")));
            entity.setPriorityLabel((String) getNested(result, "priority", "label"));
            entity.setPriorityScore(bigDecimalOrZero(getNested(result, "priority", "score")));
            entity.setRiskLevel((String) getNested(result, "risk", "level"));
            entity.setRiskScore(bigDecimalOrZero(getNested(result, "risk", "score")));
            entity.setPluginName("python-mail-intelligence");
            entity.setPluginVersion((String) result.getOrDefault("pluginVersion", "0.1.0"));
            entity.setStatus("success");
            entity.setAnalyzedAt(java.time.LocalDateTime.now());

            try {
                entity.setActionJson(objectMapper.writeValueAsString(result.getOrDefault("actions", List.of())));
            } catch (Exception ignored) {}
            try {
                entity.setReasonJson(objectMapper.writeValueAsString(result.getOrDefault("priority", Map.of())));
            } catch (Exception ignored) {}

            resultMapper.insert(entity);

            // Save threat indicators
            Object indicators = getNested(result, "risk", "indicators");
            if (indicators instanceof List<?> indicatorList) {
                for (Object ind : indicatorList) {
                    if (ind instanceof Map<?, ?> map) {
                        MailThreatIndicator ti = new MailThreatIndicator();
                        ti.setUserId(msg.getUserId());
                        ti.setMessageId(messageId);
                        ti.setIntelligenceResultId(entity.getId());
                        ti.setType((String) map.get("type"));
                        ti.setValue((String) map.get("value"));
                        ti.setRiskLevel((String) map.get("riskLevel"));
                        ti.setReason((String) map.get("reason"));
                        threatIndicatorMapper.insert(ti);
                    }
                }
            }

            // Create push events for high priority / high risk
            boolean isHighPriority = "high".equals(entity.getPriorityLabel());
            boolean isHighRisk = "high".equals(entity.getRiskLevel()) || "critical".equals(entity.getRiskLevel());

            if (isHighPriority) {
                MailPushEvent event = new MailPushEvent();
                event.setUserId(msg.getUserId());
                event.setMessageId(messageId);
                event.setEventType("high_priority");
                event.setTitle("高优先级邮件: " + msg.getSubject());
                event.setContent("来自 " + msg.getFromAddress() + " 的邮件被标记为高优先级");
                event.setPriority("high");
                event.setReadFlag(0);
                event.setPushedAt(java.time.LocalDateTime.now());
                pushEventMapper.insert(event);
            }

            if (isHighRisk) {
                MailPushEvent event = new MailPushEvent();
                event.setUserId(msg.getUserId());
                event.setMessageId(messageId);
                event.setEventType("security_alert");
                event.setTitle("安全警报: " + msg.getSubject());
                event.setContent("该邮件被检测到 " + entity.getRiskLevel() + " 风险");
                event.setPriority("high");
                event.setReadFlag(0);
                event.setPushedAt(java.time.LocalDateTime.now());
                pushEventMapper.insert(event);
            }

            return new IntelligenceAnalysisResult(
                    messageId,
                    entity.getSpamLabel(),
                    entity.getSpamScore(),
                    entity.getPriorityLabel(),
                    entity.getPriorityScore(),
                    entity.getRiskLevel(),
                    entity.getRiskScore(),
                    entity.getPluginName(),
                    entity.getPluginVersion(),
                    OffsetDateTime.now(),
                    threatIndicatorMapper.selectList(
                            new LambdaQueryWrapper<MailThreatIndicator>()
                                    .eq(MailThreatIndicator::getIntelligenceResultId, entity.getId())
                    ).stream().map(t -> new ThreatIndicator(t.getType(), t.getValue(), t.getRiskLevel(), t.getReason()))
                            .toList()
            );

        } catch (Exception e) {
            log.error("Failed to analyze message {}: {}", messageId, e.getMessage());

            // Save error result
            MailIntelligenceResult entity = new MailIntelligenceResult();
            entity.setUserId(msg.getUserId());
            entity.setMessageId(messageId);
            entity.setSpamLabel("unknown");
            entity.setSpamScore(BigDecimal.ZERO);
            entity.setPriorityLabel("normal");
            entity.setPriorityScore(BigDecimal.ZERO);
            entity.setRiskLevel("none");
            entity.setRiskScore(BigDecimal.ZERO);
            entity.setStatus("failed");
            entity.setErrorMessage(e.getMessage());
            entity.setAnalyzedAt(java.time.LocalDateTime.now());
            resultMapper.insert(entity);

            return new IntelligenceAnalysisResult(
                    messageId, "unknown", BigDecimal.ZERO,
                    "normal", BigDecimal.ZERO,
                    "none", BigDecimal.ZERO,
                    "unknown", "0.0.0",
                    OffsetDateTime.now(), List.of()
            );
        }
    }

    @Async
    @TransactionalEventListener
    public void onMessageSynced(MailMessageSyncedEvent event) {
        try {
            log.info("Auto-analyzing message {} after IMAP sync", event.getMessageId());
            analyzeMessage(event.getMessageId());
        } catch (Exception e) {
            log.error("Auto-analysis failed for message {}: {}", event.getMessageId(), e.getMessage());
        }
    }

    @Override
    public IntelligenceAnalysisResult getMessageResult(Long messageId) {
        MailIntelligenceResult entity = resultMapper.selectOne(
                new LambdaQueryWrapper<MailIntelligenceResult>()
                        .eq(MailIntelligenceResult::getMessageId, messageId)
                        .orderByDesc(MailIntelligenceResult::getCreatedAt)
                        .last("LIMIT 1")
        );
        if (entity == null) throw new IllegalArgumentException("该邮件尚未进行智能分析");

        List<ThreatIndicator> threats = threatIndicatorMapper.selectList(
                new LambdaQueryWrapper<MailThreatIndicator>()
                        .eq(MailThreatIndicator::getIntelligenceResultId, entity.getId())
        ).stream().map(t -> new ThreatIndicator(t.getType(), t.getValue(), t.getRiskLevel(), t.getReason())).toList();

        return new IntelligenceAnalysisResult(
                messageId,
                entity.getSpamLabel(),
                entity.getSpamScore(),
                entity.getPriorityLabel(),
                entity.getPriorityScore(),
                entity.getRiskLevel(),
                entity.getRiskScore(),
                entity.getPluginName(),
                entity.getPluginVersion(),
                entity.getAnalyzedAt() != null ?
                        OffsetDateTime.of(entity.getAnalyzedAt(), java.time.ZoneOffset.ofHours(8)) : null,
                threats
        );
    }

    private Object getNested(Map<String, Object> map, String... keys) {
        Object current = map;
        for (String key : keys) {
            if (current instanceof Map<?, ?> m) {
                current = m.get(key);
            } else {
                return null;
            }
        }
        return current;
    }

    private BigDecimal bigDecimalOrZero(Object val) {
        if (val instanceof Number n) return BigDecimal.valueOf(n.doubleValue());
        return BigDecimal.ZERO;
    }

    private List<String> extractLinks(String html) {
        if (html == null || html.isBlank()) return List.of();
        List<String> links = new ArrayList<>();
        java.util.regex.Pattern pattern = java.util.regex.Pattern.compile(
                "href\\s*=\\s*[\"'](https?://[^\"']+)[\"']", java.util.regex.Pattern.CASE_INSENSITIVE);
        java.util.regex.Matcher matcher = pattern.matcher(html);
        while (matcher.find()) {
            links.add(matcher.group(1));
        }
        return links;
    }
}
