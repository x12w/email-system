package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.service.MailMessageService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MailMessageServiceImpl extends ServiceImpl<MailMessageMapper, MailMessage> implements MailMessageService {
    private static final Logger log = LoggerFactory.getLogger(MailMessageServiceImpl.class);

    @Override
    public void receiveAndProcessEmail(MailMessage message) {
        log.info("收到新邮件 from={} subject={}", message.getFromAddress(), message.getSubject());
        baseMapper.insert(message);
        log.info("邮件已存入数据库 id={}", message.getId());
    }
}