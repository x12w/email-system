package com.example.emailsystem.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.example.emailsystem.entity.MailMessage;

public interface MailMessageService extends IService<MailMessage> {
    // 接收并处理新邮件
    void receiveAndProcessEmail(MailMessage message);
}