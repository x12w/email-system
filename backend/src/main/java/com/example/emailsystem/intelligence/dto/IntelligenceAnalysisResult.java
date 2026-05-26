package com.example.emailsystem.intelligence.dto;

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
    String pluginName,
    String pluginVersion,
    OffsetDateTime analyzedAt,
    List<ThreatIndicator> threats
) {
}

