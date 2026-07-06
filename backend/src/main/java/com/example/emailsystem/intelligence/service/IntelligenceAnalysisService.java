package com.example.emailsystem.intelligence.service;

import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;

public interface IntelligenceAnalysisService {

    IntelligenceAnalysisResult analyzeMessage(Long messageId);

    IntelligenceAnalysisResult getMessageResult(Long messageId);
}

