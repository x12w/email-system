package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.dto.request.SendMessageRequest;
import com.example.emailsystem.dto.response.MessageResponse;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailAttachment;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.mapper.MailAccountMapper;
import com.example.emailsystem.mapper.MailAttachmentMapper;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.mapper.MailRecipientMapper;
import com.example.emailsystem.service.MailSendService;
import com.example.emailsystem.storage.StorageService;
import com.example.emailsystem.util.AesEncryptUtil;
import jakarta.mail.*;
import jakarta.mail.internet.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.Properties;

@Service
public class MailSendServiceImpl implements MailSendService {

    private final MailAccountMapper accountMapper;
    private final MailMessageMapper messageMapper;
    private final MailRecipientMapper recipientMapper;
    private final MailAttachmentMapper attachmentMapper;
    private final AesEncryptUtil encryptUtil;
    private final StorageService storageService;

    public MailSendServiceImpl(MailAccountMapper accountMapper,
                               MailMessageMapper messageMapper,
                               MailRecipientMapper recipientMapper,
                               MailAttachmentMapper attachmentMapper,
                               AesEncryptUtil encryptUtil,
                               StorageService storageService) {
        this.accountMapper = accountMapper;
        this.messageMapper = messageMapper;
        this.recipientMapper = recipientMapper;
        this.attachmentMapper = attachmentMapper;
        this.encryptUtil = encryptUtil;
        this.storageService = storageService;
    }

    @Override
    @Transactional
    public MessageResponse send(Long userId, SendMessageRequest req) {
        MailAccount account = accountMapper.selectOne(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, req.accountId())
                        .eq(MailAccount::getUserId, userId)
        );
        if (account == null) throw new IllegalArgumentException("邮箱账号不存在");

        // Build and send via Jakarta Mail
        try {
            MimeMessage mimeMsg = buildMimeMessage(account, req);
            Transport.send(mimeMsg);
        } catch (MessagingException e) {
            throw new RuntimeException("发送邮件失败: " + e.getMessage(), e);
        }

        // Save to database
        MailMessage msg = new MailMessage();
        msg.setUserId(userId);
        msg.setAccountId(req.accountId());
        msg.setFromAddress(account.getEmailAddress());
        msg.setFromName(account.getDisplayName());
        msg.setSubject(req.subject());
        msg.setContentType(req.contentType() != null ? req.contentType() : "html");
        msg.setContent(req.content());
        msg.setPreview(stripHtml(req.content()));
        msg.setSentAt(LocalDateTime.now());
        msg.setReceivedAt(LocalDateTime.now());
        msg.setReadFlag(1);
        msg.setDraftFlag(0);
        msg.setDeletedFlag(0);

        List<MailAttachment> attachments = null;
        if (req.attachmentIds() != null && !req.attachmentIds().isEmpty()) {
            attachments = attachmentMapper.selectBatchIds(req.attachmentIds());
            msg.setAttachmentCount(attachments.size());
        }

        messageMapper.insert(msg);

        // Save recipients
        saveRecipients(msg.getId(), "to", req.to());
        if (req.cc() != null) saveRecipients(msg.getId(), "cc", req.cc());
        if (req.bcc() != null) saveRecipients(msg.getId(), "bcc", req.bcc());

        // Link attachments to message
        if (attachments != null) {
            for (MailAttachment att : attachments) {
                att.setMessageId(msg.getId());
                attachmentMapper.updateById(att);
            }
        }

        return MessageResponse.from(msg);
    }

    private MimeMessage buildMimeMessage(MailAccount account, SendMessageRequest req) throws MessagingException {
        Properties props = new Properties();
        props.put("mail.smtp.host", account.getSmtpHost());
        props.put("mail.smtp.port", account.getSmtpPort());

        if (account.getSmtpSsl() != null && account.getSmtpSsl() == 1) {
            props.put("mail.smtp.auth", "true");
            props.put("mail.smtp.ssl.enable", "true");
        } else {
            props.put("mail.smtp.auth", "true");
            props.put("mail.smtp.starttls.enable", "true");
        }

        String password = encryptUtil.decrypt(account.getAuthPasswordEncrypted());
        Session session = Session.getInstance(props, new Authenticator() {
            @Override
            protected PasswordAuthentication getPasswordAuthentication() {
                return new PasswordAuthentication(account.getAuthUsername(), password);
            }
        });

        MimeMessage mimeMsg = new MimeMessage(session);
        mimeMsg.setFrom(new InternetAddress(account.getEmailAddress(), account.getDisplayName()));
        mimeMsg.setSubject(req.subject(), "UTF-8");
        mimeMsg.setSentDate(new Date());

        // Recipients
        for (String to : req.to()) {
            mimeMsg.addRecipient(Message.RecipientType.TO, new InternetAddress(to));
        }
        if (req.cc() != null) {
            for (String cc : req.cc()) {
                if (!cc.isBlank()) mimeMsg.addRecipient(Message.RecipientType.CC, new InternetAddress(cc));
            }
        }
        if (req.bcc() != null) {
            for (String bcc : req.bcc()) {
                if (!bcc.isBlank()) mimeMsg.addRecipient(Message.RecipientType.BCC, new InternetAddress(bcc));
            }
        }

        // Content
        boolean isHtml = "html".equalsIgnoreCase(req.contentType());
        if (req.attachmentIds() != null && !req.attachmentIds().isEmpty()) {
            Multipart multipart = new MimeMultipart();
            MimeBodyPart textPart = new MimeBodyPart();
            textPart.setContent(req.content(), isHtml ? "text/html; charset=UTF-8" : "text/plain; charset=UTF-8");
            multipart.addBodyPart(textPart);

            List<MailAttachment> attachments = attachmentMapper.selectBatchIds(req.attachmentIds());
            for (MailAttachment att : attachments) {
                MimeBodyPart attachPart = new MimeBodyPart();
                var resource = storageService.loadAsResource(att.getStoragePath());
                attachPart.attachFile(resource.getFile());
                attachPart.setFileName(MimeUtility.encodeText(att.getOriginalName(), "UTF-8", null));
                multipart.addBodyPart(attachPart);
            }
            mimeMsg.setContent(multipart);
        } else {
            mimeMsg.setContent(req.content(), isHtml ? "text/html; charset=UTF-8" : "text/plain; charset=UTF-8");
        }

        return mimeMsg;
    }

    private void saveRecipients(Long messageId, String type, List<String> addresses) {
        for (String addr : addresses) {
            if (addr.isBlank()) continue;
            MailRecipient r = new MailRecipient();
            r.setMessageId(messageId);
            r.setType(type);
            r.setEmailAddress(addr);
            recipientMapper.insert(r);
        }
    }

    private String stripHtml(String html) {
        if (html == null) return "";
        return html.replaceAll("<[^>]*>", "")
                   .replaceAll("\\s+", " ")
                   .trim();
    }
}
