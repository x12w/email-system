package com.example.emailsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.example.emailsystem.entity.MailIntelligenceResult;

public interface MailIntelligenceResultService extends IService<MailIntelligenceResult> {
    // 定义一个保存分析结果的业务方法
    void saveAnalysisResult(MailIntelligenceResult result);
}