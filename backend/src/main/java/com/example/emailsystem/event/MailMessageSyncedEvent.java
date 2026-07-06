package com.example.emailsystem.event;

import lombok.Getter;

@Getter
public class MailMessageSyncedEvent {

    private final Long messageId;
    private final Long userId;

    public MailMessageSyncedEvent(Long messageId, Long userId) {
        this.messageId = messageId;
        this.userId = userId;
    }
}
