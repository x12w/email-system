package com.example.emailsystem.intelligence.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "intelligence.llm")
public record IntelligenceLlmProperties(
    boolean enabled,
    String baseUrl,
    String apiKey,
    String model,
    int timeoutSeconds
) {
    public IntelligenceLlmProperties {
        if (timeoutSeconds <= 0) timeoutSeconds = 30;
    }
}
