package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailIntelligenceResult; // 导入 AI 实体
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.service.MailMessageService;
import com.example.emailsystem.service.MailIntelligenceResultService; // 导入 AI 服务
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional; // 导入事务

@Slf4j
@Service
public class MailMessageServiceImpl extends ServiceImpl<MailMessageMapper, MailMessage> implements MailMessageService {

    @Autowired
    private MailIntelligenceResultService intelligenceService; // 👈 注入刚刚建好的 AI 服务

    @Override
    @Transactional(rollbackFor = Exception.class) // 👈 涉及多表操作，开启声明式事务
    public void receiveAndProcessEmail(MailMessage message) {
        log.info("【邮件服务】开始处理新邮件接收流程...");

        // 1. 基础参数校验（回应核心关于 user_id、account_id、from_address 必填的要求）
        if (message.getUserId() == null || message.getAccountId() == null || message.getFromAddress() == null) {
            log.error("【邮件服务】入库失败：缺少必要参数！");
            throw new IllegalArgumentException("邮件必填参数缺失：user_id, account_id, from_address 不能为空");
        }

        // 2. 邮件基础数据入库
        baseMapper.insert(message);
        log.info("【邮件服务】邮件基础数据入库成功，邮件ID: {}", message.getId());

        // 3. 业务编排：模拟智能分析任务并保存结果（回应核心关于 docs/07 文档的调用链要求）
        log.info("【邮件服务】触发智能分析任务流...");
        
        MailIntelligenceResult aiResult = new MailIntelligenceResult();
        aiResult.setMessageId(message.getId());
        aiResult.setSpamScore(java.math.BigDecimal.valueOf(0.15));
        aiResult.setStatus("PASSED");       // 模拟 AI 状态：通过
        
        // 👈 调用专门的 AI Service 执行结果入库，不再跨界乱写
        intelligenceService.saveAnalysisResult(aiResult);
        log.info("【邮件服务】智能分析结果保存成功，邮件处理流结束。");
    }
}