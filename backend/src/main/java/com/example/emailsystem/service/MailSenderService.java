package com.example.emailsystem.service;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.mapper.MailRecipientMapper;
import jakarta.mail.internet.MimeMessage;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
public class MailSenderService {
    private static final Logger log = LoggerFactory.getLogger(MailSenderService.class);

    private final MailMessageMapper mailMessageMapper;
    private final MailRecipientMapper mailRecipientMapper;
    private final MailFolderService mailFolderService;

    public MailSenderService(MailMessageMapper mailMessageMapper,
                             MailRecipientMapper mailRecipientMapper,
                             MailFolderService mailFolderService) {
        this.mailMessageMapper = mailMessageMapper;
        this.mailRecipientMapper = mailRecipientMapper;
        this.mailFolderService = mailFolderService;
    }

    public MailMessage send(MailAccount account, String subject, String contentType, String content,
                            List<String> to, List<String> cc, List<String> bcc,
                            List<Long> attachmentIds, Long userId) {
        // 1. 通过 SMTP 发送
        JavaMailSender mailSender = buildMailSender(account);
        try {
            MimeMessage mimeMessage = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");
            helper.setFrom(account.getEmailAddress(), account.getDisplayName());
            helper.setSubject(subject);
            helper.setText(content, "html".equals(contentType));
            if (to != null) {
                for (String addr : to) {
                    if (!addr.isBlank()) helper.addTo(addr.trim());
                }
            }
            if (cc != null) {
                for (String addr : cc) {
                    if (!addr.isBlank()) helper.addCc(addr.trim());
                }
            }
            if (bcc != null) {
                for (String addr : bcc) {
                    if (!addr.isBlank()) helper.addBcc(addr.trim());
                }
            }
            mailSender.send(mimeMessage);
            log.info("邮件已通过 SMTP 发送: {} -> {}", account.getEmailAddress(), to);
        } catch (Exception e) {
            log.error("SMTP 发送失败", e);
            throw new BusinessException("MAIL_400", "邮件发送失败: " + e.getMessage());
        }

        // 2. 持久化到数据库
        MailMessage message = new MailMessage();
        message.setUserId(userId);
        message.setAccountId(account.getId());
        message.setFolderId(mailFolderService.getOrCreateSentFolder(account.getId(), userId).getId());
        message.setFromAddress(account.getEmailAddress());
        message.setFromName(account.getDisplayName());
        message.setSubject(subject);
        message.setContentType(contentType == null ? "html" : contentType);
        message.setContent(content);
        message.setPreview(extractPreview(content));
        message.setSentAt(LocalDateTime.now());
        message.setReceivedAt(LocalDateTime.now());
        message.setReadFlag(1);
        message.setStarFlag(0);
        message.setDraftFlag(0);
        message.setDeletedFlag(0);
        message.setAttachmentCount(attachmentIds == null ? 0 : attachmentIds.size());
        message.setCreatedAt(LocalDateTime.now());
        message.setUpdatedAt(LocalDateTime.now());
        mailMessageMapper.insert(message);

        // 3. 保存收件人
        saveRecipients(message.getId(), "to", to);
        saveRecipients(message.getId(), "cc", cc);
        saveRecipients(message.getId(), "bcc", bcc);

        return message;
    }

    public MailMessage saveDraft(MailAccount account, String subject, String contentType, String content,
                                 List<String> to, List<String> cc, List<String> bcc,
                                 List<Long> attachmentIds, Long userId) {
        MailMessage message = new MailMessage();
        message.setUserId(userId);
        message.setAccountId(account.getId());
        message.setFolderId(mailFolderService.getOrCreateDraftFolder(account.getId(), userId).getId());
        message.setFromAddress(account.getEmailAddress());
        message.setFromName(account.getDisplayName());
        message.setSubject(subject);
        message.setContentType(contentType == null ? "html" : contentType);
        message.setContent(content);
        message.setPreview(extractPreview(content));
        message.setSentAt(LocalDateTime.now());
        message.setReceivedAt(LocalDateTime.now());
        message.setReadFlag(1);
        message.setStarFlag(0);
        message.setDraftFlag(1);
        message.setDeletedFlag(0);
        message.setAttachmentCount(attachmentIds == null ? 0 : attachmentIds.size());
        message.setCreatedAt(LocalDateTime.now());
        message.setUpdatedAt(LocalDateTime.now());
        mailMessageMapper.insert(message);

        saveRecipients(message.getId(), "to", to);
        saveRecipients(message.getId(), "cc", cc);
        saveRecipients(message.getId(), "bcc", bcc);

        return message;
    }

    private void saveRecipients(Long messageId, String type, List<String> addresses) {
        if (addresses == null) return;
        for (String addr : addresses) {
            if (addr == null || addr.isBlank()) continue;
            MailRecipient recipient = new MailRecipient();
            recipient.setMessageId(messageId);
            recipient.setType(type);
            recipient.setEmailAddress(addr.trim().toLowerCase());
            mailRecipientMapper.insert(recipient);
        }
    }

    private JavaMailSender buildMailSender(MailAccount account) {
        JavaMailSenderImpl sender = new JavaMailSenderImpl();
        sender.setHost(account.getSmtpHost());
        sender.setPort(account.getSmtpPort() != null ? account.getSmtpPort() : 25);
        sender.setUsername(account.getAuthUsername());
        sender.setPassword(account.getAuthPasswordEncrypted());
        sender.getJavaMailProperties().put("mail.smtp.auth", "true");
        sender.getJavaMailProperties().put("mail.smtp.starttls.enable",
            account.getSmtpSsl() != null && account.getSmtpSsl() == 1 ? "true" : "false");
        return sender;
    }

    private String extractPreview(String content) {
        if (content == null) return "";
        String plain = content.replaceAll("<[^>]+>", "").strip();
        return plain.length() > 120 ? plain.substring(0, 120) : plain;
    }
}
