package com.example.emailsystem.intelligence.plugin;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class RuleBasedIntelligencePluginClient implements IntelligencePluginClient {
    private final ObjectMapper objectMapper;

    public RuleBasedIntelligencePluginClient(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @Override
    public String analyzeEmailJson(String requestJson) {
        try {
            Map<?, ?> payload = objectMapper.readValue(requestJson, Map.class);
            String subject = String.valueOf(payload.get("subject") == null ? "" : payload.get("subject"));
            String plainText = String.valueOf(payload.get("plainText") == null ? "" : payload.get("plainText"));
            String text = (subject + "\n" + plainText).toLowerCase(Locale.ROOT);
            List<String> links = readLinks(payload.get("links"));
            List<Map<String, String>> indicators = detectLinks(links);
            double priorityScore = score(text, List.of("urgent", "紧急", "审批", "故障", "投诉", "合同", "到期"));
            double spamScore = score(text, List.of("中奖", "免费", "返利", "贷款", "casino", "winner"));
            double riskScore = Math.min(1.0, indicators.size() * 0.35);
            String riskLevel = riskScore >= 0.75 ? "high" : riskScore >= 0.5 ? "medium" : riskScore > 0 ? "low" : "none";
            String spamLabel = spamScore >= 0.6 ? "spam" : "normal";
            String priorityLabel = priorityScore >= 0.5 ? "high" : "normal";
            List<String> actions = new ArrayList<>();
            if ("high".equals(priorityLabel) && !"spam".equals(spamLabel)) {
                actions.add("mark_high_priority");
                actions.add("push_notification");
            }
            if (List.of("high", "critical").contains(riskLevel)) {
                actions.add("push_security_alert");
            }
            return objectMapper.writeValueAsString(Map.of(
                "pluginVersion", "0.1.0",
                "spam", Map.of("label", spamLabel, "score", spamScore),
                "priority", Map.of("label", priorityLabel, "score", priorityScore, "reasons", actions),
                "risk", Map.of("level", riskLevel, "score", riskScore, "indicators", indicators),
                "actions", actions
            ));
        } catch (Exception exception) {
            return "{\"pluginVersion\":\"0.1.0\",\"spam\":{\"label\":\"unknown\",\"score\":0},\"priority\":{\"label\":\"normal\",\"score\":0,\"reasons\":[]},\"risk\":{\"level\":\"none\",\"score\":0,\"indicators\":[]},\"actions\":[]}";
        }
    }

    private double score(String text, List<String> keywords) {
        long hits = keywords.stream().filter(keyword -> text.contains(keyword.toLowerCase(Locale.ROOT))).count();
        return Math.min(1.0, hits / 2.0);
    }

    private List<String> readLinks(Object rawLinks) {
        if (!(rawLinks instanceof List<?> values)) {
            return List.of();
        }
        return values.stream().map(String::valueOf).toList();
    }

    private List<Map<String, String>> detectLinks(List<String> links) {
        List<Map<String, String>> indicators = new ArrayList<>();
        for (String link : links) {
            String lowered = link.toLowerCase(Locale.ROOT);
            if (lowered.matches("https?://\\d+\\.\\d+\\.\\d+\\.\\d+.*")) {
                indicators.add(Map.of("type", "url", "value", link, "riskLevel", "medium", "reason", "url uses ip address host"));
            }
            if (lowered.contains("login") || lowered.contains("password") || lowered.contains("pay") || lowered.contains("verify")) {
                indicators.add(Map.of("type", "url", "value", link, "riskLevel", "medium", "reason", "sensitive action keyword in url"));
            }
        }
        return indicators;
    }
}
