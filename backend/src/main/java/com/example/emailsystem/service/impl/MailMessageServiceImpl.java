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
    private MailIntelligenceResultService intelligenceService; // 👈 注入建好的 AI 服务

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

        // 3. 业务编排：根据组长整改要求，补齐非空字段，将分析状态记录为 skipped，消除硬编码模拟 AI 结果
        log.info("【邮件服务】触发智能分析任务流...");
        
        MailIntelligenceResult aiResult = new MailIntelligenceResult();
        
        // 【整改 1：设置数据库必填的非空字段】
        aiResult.setUserId(message.getUserId());                   // 👈 补齐 user_id
        aiResult.setMessageId(message.getId());                    // 👈 关联邮件自增ID
        aiResult.setPluginName("python-mail-intelligence");       // 👈 补齐规范定义的默认插件名
        aiResult.setPluginVersion("0.1.0");                       // 👈 补齐预设插件版本

        // 【整改 2：使用规范枚举值 skipped，坚决不用未定义的 PASSED】
        aiResult.setStatus("skipped");       

        // 【整改 3：补齐业务默认值，避免实体状态依赖数据库默认值而不清晰】
        aiResult.setSpamLabel("unknown");                          // 垃圾邮件标签初始化为未知
        aiResult.setSpamScore(java.math.BigDecimal.ZERO);          // 分数初始化为 0
        aiResult.setPriorityLabel("normal");                       // 优先级标签默认普通
        aiResult.setPriorityScore(java.math.BigDecimal.ZERO);
        aiResult.setRiskLevel("none");                             // 风险等级默认无风险
        aiResult.setRiskScore(java.math.BigDecimal.ZERO);
        
        // 👈 调用专门的 AI Service 执行结果入库
        intelligenceService.saveAnalysisResult(aiResult);
        log.info("【邮件服务】智能分析结果保存成功（当前记录为 skipped），邮件处理流结束。");
    }
}