package com.example.emailsystem.intelligence.client;

import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;

public interface IntelligenceClient {

    IntelligenceAnalysisResult analyze(MailMessage message);
}
