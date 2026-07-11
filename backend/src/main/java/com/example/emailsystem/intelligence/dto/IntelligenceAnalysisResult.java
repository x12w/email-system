package com.example.emailsystem.intelligence.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

public record IntelligenceAnalysisResult(
    Long messageId,
    String spamLabel,
    BigDecimal spamScore,
    String priorityLabel,
    BigDecimal priorityScore,
    String riskLevel,
    BigDecimal riskScore,
    @JsonProperty("pluginName") String analyzerName,
    @JsonProperty("pluginVersion") String analyzerVersion,
    OffsetDateTime analyzedAt,
    List<ThreatIndicator> threats
) {
}

