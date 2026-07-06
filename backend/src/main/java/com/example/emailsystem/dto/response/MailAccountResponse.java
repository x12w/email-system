package com.example.emailsystem.dto.response;

import com.example.emailsystem.entity.MailAccount;

import java.time.LocalDateTime;

public record MailAccountResponse(
        Long id,
        String emailAddress,
        String displayName,
        String smtpHost,
        Integer smtpPort,
        Integer smtpSsl,
        String imapHost,
        Integer imapPort,
        Integer imapSsl,
        String authUsername,
        Integer status,
        LocalDateTime lastSyncAt,
        LocalDateTime createdAt
) {
    public static MailAccountResponse from(MailAccount acct) {
        return new MailAccountResponse(
                acct.getId(), acct.getEmailAddress(), acct.getDisplayName(),
                acct.getSmtpHost(), acct.getSmtpPort(), acct.getSmtpSsl(),
                acct.getImapHost(), acct.getImapPort(), acct.getImapSsl(),
                acct.getAuthUsername(), acct.getStatus(), acct.getLastSyncAt(),
                acct.getCreatedAt()
        );
    }
}
