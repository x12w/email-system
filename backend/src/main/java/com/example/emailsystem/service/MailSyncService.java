package com.example.emailsystem.service;

import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailFolder;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.mapper.MailRecipientMapper;
import jakarta.mail.Flags;
import jakarta.mail.Folder;
import jakarta.mail.Message;
import jakarta.mail.Session;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.List;
import java.util.Properties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
public class MailSyncService {
    private static final Logger log = LoggerFactory.getLogger(MailSyncService.class);

    private final MailAccountService mailAccountService;
    private final MailFolderService mailFolderService;
    private final MailMessageMapper mailMessageMapper;
    private final MailRecipientMapper mailRecipientMapper;

    public MailSyncService(MailAccountService mailAccountService,
                           MailFolderService mailFolderService,
                           MailMessageMapper mailMessageMapper,
                           MailRecipientMapper mailRecipientMapper) {
        this.mailAccountService = mailAccountService;
        this.mailFolderService = mailFolderService;
        this.mailMessageMapper = mailMessageMapper;
        this.mailRecipientMapper = mailRecipientMapper;
    }

    /**
     * 定时同步所有活跃邮箱的 INBOX 邮件（每 60 秒）
     */
    @Scheduled(fixedDelay = 60000)
    public void syncAllAccounts() {
        // 简化实现：同步 userId=1 的所有账号
        syncUserAccounts(1L);
    }

    public void syncUserAccounts(Long userId) {
        new Thread(() -> {
            List<MailAccount> accounts = mailAccountService.listAccounts(userId);
            for (MailAccount account : accounts) {
                try {
                    int count = syncInbox(account);
                    if (count > 0) {
                        log.info("IMAP 同步完成 account={}: {} 封新邮件", account.getEmailAddress(), count);
                    }
                } catch (Exception e) {
                    log.warn("IMAP 同步失败 account={}: {}", account.getEmailAddress(), e.getMessage());
                }
            }
        }, "imap-sync-user-" + userId).start();
    }

    public int syncInbox(MailAccount account) {
        if (account.getImapHost() == null || account.getImapHost().isBlank()
            || account.getImapPort() == null) {
            return 0;
        }
        int count = 0;
        Properties props = new Properties();
        props.put("mail.store.protocol", "imaps");
        props.put("mail.imaps.host", account.getImapHost());
        props.put("mail.imaps.port", String.valueOf(account.getImapPort()));
        props.put("mail.imaps.auth", "true");
        props.put("mail.imaps.timeout", "15000");
        props.put("mail.imaps.connectiontimeout", "10000");

        try {
            Session session = Session.getInstance(props);
            jakarta.mail.Store store = session.getStore("imaps");
            store.connect(account.getImapHost(), account.getAuthUsername(), account.getAuthPasswordEncrypted());

            // Gmail 的 INBOX 不包含其他标签页的邮件，用 [Gmail]/All Mail 获取全部
            Folder inbox;
            try {
                inbox = store.getFolder("[Gmail]/All Mail");
                inbox.open(Folder.READ_ONLY);
            } catch (Exception e) {
                inbox = store.getFolder("INBOX");
                inbox.open(Folder.READ_WRITE);
            }

            MailFolder inboxFolder = mailFolderService.getOrCreateInboxFolder(
                account.getId(), account.getUserId());

            // 首次同步仅拉取最近 7 天；后续同步拉取上次同步之后的
            java.util.Date since;
            if (account.getLastSyncAt() != null) {
                since = java.util.Date.from(account.getLastSyncAt()
                    .atZone(java.time.ZoneId.systemDefault()).toInstant());
            } else {
                var cal = java.util.Calendar.getInstance();
                cal.add(java.util.Calendar.DAY_OF_MONTH, -7);
                since = cal.getTime();
            }

            Message[] messages = inbox.getMessages();
            for (Message msg : messages) {
                if (msg.getReceivedDate() != null && msg.getReceivedDate().before(since)) {
                    continue; // 跳过旧邮件
                }
                String msgId = ((MimeMessage) msg).getMessageID();
                if (msgId != null && mailMessageMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<MailMessage>()
                        .eq("message_id", msgId)) > 0) {
                    continue;
                }
                MimeMessage mimeMsg = (MimeMessage) msg;
                MailMessage mailMessage = new MailMessage();
                mailMessage.setUserId(account.getUserId());
                mailMessage.setAccountId(account.getId());
                mailMessage.setFolderId(inboxFolder.getId());

                InternetAddress from = (InternetAddress) mimeMsg.getFrom()[0];
                mailMessage.setMessageUid(msgId);
                mailMessage.setMessageId(msgId);
                mailMessage.setFromAddress(from.getAddress());
                mailMessage.setFromName(from.getPersonal());
                mailMessage.setSubject(mimeMsg.getSubject() == null ? "" : mimeMsg.getSubject());
                mailMessage.setContentType("html");
                mailMessage.setContent(extractContent(mimeMsg));
                mailMessage.setPreview(extractPreview(mailMessage.getContent()));
                mailMessage.setSentAt(toLocalDateTime(mimeMsg.getSentDate()));
                mailMessage.setReceivedAt(toLocalDateTime(mimeMsg.getReceivedDate()));
                mailMessage.setReadFlag(0);
                mailMessage.setStarFlag(0);
                mailMessage.setDraftFlag(0);
                mailMessage.setDeletedFlag(0);
                mailMessage.setAttachmentCount(0);
                mailMessage.setCreatedAt(LocalDateTime.now());
                mailMessage.setUpdatedAt(LocalDateTime.now());
                mailMessageMapper.insert(mailMessage);

                // 保存收件人
                if (mimeMsg.getRecipients(Message.RecipientType.TO) != null) {
                    for (jakarta.mail.Address addr : mimeMsg.getRecipients(Message.RecipientType.TO)) {
                        saveRecipient(mailMessage.getId(), "to", (InternetAddress) addr);
                    }
                }

                // 标记为已读（已同步）
                msg.setFlag(Flags.Flag.SEEN, true);
                count++;
            }
            inbox.close(false);
            store.close();

            account.setLastSyncAt(LocalDateTime.now());
            mailAccountService.updateLastSync(account);

            if (count > 0) {
                mailFolderService.updateCounts(inboxFolder.getId(), count, count);
                log.info("IMAP 同步完成 account={}: {} 封新邮件", account.getEmailAddress(), count);
            }
        } catch (Exception e) {
            log.error("IMAP 同步异常 account={}: {}", account.getEmailAddress(), e.getMessage());
        }
        return count;
    }

    private void saveRecipient(Long messageId, String type, InternetAddress addr) {
        MailRecipient recipient = new MailRecipient();
        recipient.setMessageId(messageId);
        recipient.setType(type);
        recipient.setEmailAddress(addr.getAddress().toLowerCase());
        recipient.setDisplayName(addr.getPersonal());
        mailRecipientMapper.insert(recipient);
    }

    private String extractContent(MimeMessage msg) throws Exception {
        try {
            Object content = msg.getContent();
            if (content instanceof String) {
                return (String) content;
            }
            if (content instanceof MimeMultipart multipart) {
                for (int i = 0; i < multipart.getCount(); i++) {
                    var part = multipart.getBodyPart(i);
                    if (part.isMimeType("text/html") || part.isMimeType("text/plain")) {
                        Object partContent = part.getContent();
                        if (partContent instanceof String) {
                            return (String) partContent;
                        }
                    }
                }
            }
            return content.toString();
        } catch (Exception e) {
            return "";
        }
    }

    private String extractPreview(String content) {
        if (content == null) return "";
        String plain = content.replaceAll("<[^>]+>", "").strip();
        return plain.length() > 120 ? plain.substring(0, 120) : plain;
    }

    private LocalDateTime toLocalDateTime(java.util.Date date) {
        if (date == null) return LocalDateTime.now();
        return date.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
    }
}
