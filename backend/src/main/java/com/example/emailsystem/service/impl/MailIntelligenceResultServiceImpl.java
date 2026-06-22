package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.emailsystem.entity.MailIntelligenceResult;
import com.example.emailsystem.mapper.MailIntelligenceResultMapper;
import com.example.emailsystem.service.MailIntelligenceResultService;
import org.springframework.stereotype.Service;

@Service
public class MailIntelligenceResultServiceImpl extends ServiceImpl<MailIntelligenceResultMapper, MailIntelligenceResult> implements MailIntelligenceResultService {
    
    @Override
    public void saveAnalysisResult(MailIntelligenceResult result) {
        // 调用底层的 mapper 把 AI 结果存入数据库
        baseMapper.insert(result);
    }
}