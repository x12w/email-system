package com.example.emailsystem.intelligence.dto;

public record ThreatIndicator(
    String type,
    String value,
    String riskLevel,
    String reason
) {
}

