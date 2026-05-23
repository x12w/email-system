package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.service.MailMessageService;
import org.springframework.stereotype.Service;

@Service // 必须加这个注解，告诉 Spring Boot 这是一个业务实现类，它才会帮你管理
public class MailMessageServiceImpl extends ServiceImpl<MailMessageMapper, MailMessage> implements MailMessageService {

    @Override
    public void receiveAndProcessEmail(MailMessage message) {
        // 打印两条日志，方便我们在控制台看效果
        System.out.println("【后端提示】收到新邮件，准备进行 AI 垃圾拦截...");
        
        // 使用 MyBatis-Plus 自动赠送的 baseMapper 把邮件直接存入 MySQL 数据库
        baseMapper.insert(message);
        
        System.out.println("【后端提示】邮件已成功存入 MySQL 数据库！");
    }
}