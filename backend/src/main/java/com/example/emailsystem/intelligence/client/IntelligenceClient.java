package com.example.emailsystem.intelligence.client;

import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;

public interface IntelligenceClient {

    /** Analyze using server-default LLM configuration. */
    IntelligenceAnalysisResult analyze(MailMessage message);

    /** Analyze using custom LLM configuration (user-provided API). */
    IntelligenceAnalysisResult analyze(MailMessage message, String baseUrl, String apiKey, String model);
}
