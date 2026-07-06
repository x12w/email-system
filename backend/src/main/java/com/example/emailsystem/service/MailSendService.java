package com.example.emailsystem.service;

import com.example.emailsystem.dto.request.SendMessageRequest;
import com.example.emailsystem.dto.response.MessageResponse;

public interface MailSendService {
    MessageResponse send(Long userId, SendMessageRequest req);
}
