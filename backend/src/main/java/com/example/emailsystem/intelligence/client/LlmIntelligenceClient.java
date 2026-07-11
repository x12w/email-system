package com.example.emailsystem.intelligence.client;

import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.intelligence.config.IntelligenceLlmProperties;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class LlmIntelligenceClient implements IntelligenceClient {

    private static final Logger log = LoggerFactory.getLogger(LlmIntelligenceClient.class);
    private static final int MAX_CONTENT_CHARS = 3000;

    private final RestClient restClient;
    private final IntelligenceLlmProperties properties;
    private final ObjectMapper objectMapper;

    public LlmIntelligenceClient(RestClient intelligenceRestClient,
                                 IntelligenceLlmProperties properties,
                                 ObjectMapper objectMapper) {
        this.restClient = intelligenceRestClient;
        this.properties = properties;
        this.objectMapper = objectMapper;
    }

    @Override
    public IntelligenceAnalysisResult analyze(MailMessage message) {
        if (!properties.enabled()) {
            return safeDefault(message.getId());
        }
        try {
            return doAnalyze(message, restClient, properties.model());
        } catch (Exception e) {
            log.warn("LLM analysis failed for message {}, falling back to safe default: {}",
                message.getId(), e.getMessage());
            return safeDefault(message.getId());
        }
    }

    @Override
    public IntelligenceAnalysisResult analyze(MailMessage message, String baseUrl, String apiKey, String model) {
        try {
            RestClient customClient = RestClient.create()
                .mutate()
                .defaultHeader("Authorization", "Bearer " + apiKey)
                .defaultHeader("Content-Type", "application/json")
                .build();
            return doAnalyze(message, customClient, model, baseUrl);
        } catch (Exception e) {
            log.warn("Custom LLM analysis failed for message {}, falling back to safe default: {}",
                message.getId(), e.getMessage());
            return safeDefault(message.getId());
        }
    }

    private IntelligenceAnalysisResult doAnalyze(MailMessage message, RestClient client, String model) {
        return doAnalyze(message, client, model, null);
    }

    private IntelligenceAnalysisResult doAnalyze(MailMessage message, RestClient client, String model, String baseUrlOverride) {
        String systemPrompt = buildSystemPrompt();
        String userPrompt = buildUserPrompt(message);
        String llmResponse = callLlm(client, systemPrompt, userPrompt, model, baseUrlOverride);
        return parseResponse(message.getId(), model, llmResponse);
    }

    private String buildSystemPrompt() {
        return """
            You are an email security and priority analyst. Your task is to analyze emails \
            and return a structured JSON assessment.

            Analyze the email for:
            1. SPAM detection - phishing, scams, unsolicited bulk, malicious content
            2. PRIORITY assessment - urgency, business importance, deadlines, VIP senders
            3. RISK analysis - suspicious links, credential theft, malware indicators, social engineering

            Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
            {
              "spam": {"label": "normal|spam", "score": 0.0-1.0},
              "priority": {"label": "normal|high", "score": 0.0-1.0},
              "risk": {"level": "none|low|medium|high|critical", "score": 0.0-1.0, "indicators": []},
              "actions": []
            }

            For indicators, use this structure per item:
            {"type": "url|domain|keyword|attachment|header", "value": "the matched value", \
            "riskLevel": "low|medium|high|critical", "reason": "brief explanation"}

            For actions, choose from: "mark_high_priority", "push_notification", "push_security_alert"

            The email may contain Chinese and English mixed content. \
            Score confidence based on clear indicators, not vague similarity.""";
    }

    String buildUserPrompt(MailMessage message) {
        StringBuilder sb = new StringBuilder();
        sb.append("Subject: ").append(message.getSubject()).append("\n");
        sb.append("From: ").append(message.getFromAddress()).append("\n");
        sb.append("Content:\n");
        String plainText = extractPlainText(message.getContent());
        if (plainText.length() > MAX_CONTENT_CHARS) {
            plainText = plainText.substring(0, MAX_CONTENT_CHARS);
            log.debug("Email content truncated to {} chars for message {}", MAX_CONTENT_CHARS, message.getId());
        }
        sb.append(plainText).append("\n");

        List<String> links = extractLinks(message.getContent());
        if (!links.isEmpty()) {
            sb.append("\nLinks found in email:\n");
            for (String link : links) {
                sb.append("- ").append(link).append("\n");
            }
        }
        return sb.toString();
    }

    String extractPlainText(String html) {
        if (html == null || html.isBlank()) {
            return "";
        }
        // Strip HTML tags, decode common entities, collapse whitespace
        String text = html.replaceAll("<[^>]*>", " ");
        text = text.replace("&amp;", "&")
                   .replace("&lt;", "<")
                   .replace("&gt;", ">")
                   .replace("&quot;", "\"")
                   .replace("&#39;", "'")
                   .replace("&nbsp;", " ");
        text = text.replaceAll("\\s+", " ").trim();
        return text;
    }

    List<String> extractLinks(String content) {
        List<String> links = new ArrayList<>();
        if (content == null) return links;
        for (String token : content.split("[\\s<>\"')]+")) {
            String cleaned = token.trim();
            if ((cleaned.startsWith("http://") || cleaned.startsWith("https://")) && cleaned.length() > 10) {
                links.add(cleaned);
            }
        }
        return links;
    }

    private String callLlm(RestClient client, String systemPrompt, String userPrompt,
                           String model, String baseUrlOverride) {
        Map<String, Object> requestBody = new java.util.HashMap<>(Map.of(
            "model", model,
            "temperature", 0.1,
            "messages", List.of(
                Map.of("role", "system", "content", systemPrompt),
                Map.of("role", "user", "content", userPrompt)
            )
        ));
        String uri = (baseUrlOverride != null ? baseUrlOverride : "") + "/chat/completions";
        try {
            requestBody.put("response_format", Map.of("type", "json_object"));
            String requestJson = objectMapper.writeValueAsString(requestBody);
            String response = client.post()
                .uri(uri)
                .body(requestJson)
                .retrieve()
                .body(String.class);
            if (response == null || response.isBlank()) {
                throw new RuntimeException("Empty response from LLM");
            }
            return response;
        } catch (Exception e) {
            log.debug("LLM call with json_object format failed, retrying without: {}", e.getMessage());
            requestBody.remove("response_format");
            String requestJson;
            try {
                requestJson = objectMapper.writeValueAsString(requestBody);
            } catch (Exception ex) {
                throw new RuntimeException("Failed to serialize request", ex);
            }
            String response = client.post()
                .uri(uri)
                .body(requestJson)
                .retrieve()
                .body(String.class);
            if (response == null || response.isBlank()) {
                throw new RuntimeException("Empty response from LLM");
            }
            return response;
        }
    }

    IntelligenceAnalysisResult parseResponse(Long messageId, String model, String llmResponse) {
        try {
            JsonNode root = objectMapper.readTree(llmResponse);
            JsonNode content = root.path("choices").get(0).path("message").path("content");
            String contentText = content.asText();

            // Some models wrap JSON in markdown code fences
            contentText = stripCodeFences(contentText);

            JsonNode result = objectMapper.readTree(contentText);

            JsonNode spam = result.path("spam");
            JsonNode priority = result.path("priority");
            JsonNode risk = result.path("risk");

            List<ThreatIndicator> threats = new ArrayList<>();
            for (JsonNode indicator : risk.path("indicators")) {
                threats.add(new ThreatIndicator(
                    indicator.path("type").asText("unknown"),
                    indicator.path("value").asText(""),
                    indicator.path("riskLevel").asText("low"),
                    indicator.path("reason").asText("")
                ));
            }

            return new IntelligenceAnalysisResult(
                messageId,
                spam.path("label").asText("normal"),
                BigDecimal.valueOf(clamp(spam.path("score").asDouble(0), 0, 1)),
                priority.path("label").asText("normal"),
                BigDecimal.valueOf(clamp(priority.path("score").asDouble(0), 0, 1)),
                risk.path("level").asText("none"),
                BigDecimal.valueOf(clamp(risk.path("score").asDouble(0), 0, 1)),
                model,
                "1.0.0",
                OffsetDateTime.now(),
                threats
            );
        } catch (Exception e) {
            log.warn("Failed to parse LLM response for message {}, using safe default: {}",
                messageId, e.getMessage());
            return safeDefault(messageId, model);
        }
    }

    private String stripCodeFences(String text) {
        String trimmed = text.trim();
        if (trimmed.startsWith("```")) {
            int start = trimmed.indexOf('\n');
            if (start < 0) start = 3;
            else start = start + 1;
            int end = trimmed.lastIndexOf("```");
            if (end > start) {
                return trimmed.substring(start, end).trim();
            }
            return trimmed.substring(start).trim();
        }
        return trimmed;
    }

    private IntelligenceAnalysisResult safeDefault(Long messageId) {
        return safeDefault(messageId, properties.model());
    }

    private IntelligenceAnalysisResult safeDefault(Long messageId, String model) {
        return new IntelligenceAnalysisResult(
            messageId,
            "normal", BigDecimal.ZERO,
            "normal", BigDecimal.ZERO,
            "none", BigDecimal.ZERO,
            model, "1.0.0",
            OffsetDateTime.now(),
            List.of()
        );
    }

    private static double clamp(double value, double min, double max) {
        return Math.max(min, Math.min(max, value));
    }
}
