package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.entity.MailFolder;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.mapper.MailAccountMapper;
import com.example.emailsystem.mapper.MailFolderMapper;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.mapper.MailRecipientMapper;
import com.example.emailsystem.service.ImapSyncService;
import com.example.emailsystem.util.AesEncryptUtil;
import jakarta.mail.*;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;
import jakarta.mail.internet.MimeUtility;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.Properties;

@Service
public class ImapSyncServiceImpl implements ImapSyncService {

    private final MailAccountMapper accountMapper;
    private final MailFolderMapper folderMapper;
    private final MailMessageMapper messageMapper;
    private final MailRecipientMapper recipientMapper;
    private final AesEncryptUtil encryptUtil;

    public ImapSyncServiceImpl(MailAccountMapper accountMapper,
                               MailFolderMapper folderMapper,
                               MailMessageMapper messageMapper,
                               MailRecipientMapper recipientMapper,
                               AesEncryptUtil encryptUtil) {
        this.accountMapper = accountMapper;
        this.folderMapper = folderMapper;
        this.messageMapper = messageMapper;
        this.recipientMapper = recipientMapper;
        this.encryptUtil = encryptUtil;
    }

    @Override
    @Transactional
    public void syncAccount(Long userId, Long accountId) {
        MailAccount account = accountMapper.selectOne(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, accountId)
                        .eq(MailAccount::getUserId, userId)
        );
        if (account == null) throw new IllegalArgumentException("邮箱账号不存在");

        Properties props = new Properties();
        props.put("mail.store.protocol", "imap");
        props.put("mail.imap.host", account.getImapHost());
        props.put("mail.imap.port", account.getImapPort());
        if (account.getImapSsl() != null && account.getImapSsl() == 1) {
            props.put("mail.imap.ssl.enable", "true");
            props.put("mail.imap.ssl.trust", "*");
        } else {
            props.put("mail.imap.starttls.enable", "true");
        }
        props.put("mail.imap.connectiontimeout", "10000");
        props.put("mail.imap.timeout", "10000");

        String password = encryptUtil.decrypt(account.getAuthPasswordEncrypted());

        try {
            Session session = Session.getInstance(props);
            Store store = session.getStore("imap");
            store.connect(account.getImapHost(), account.getImapPort(), account.getAuthUsername(), password);

            Folder defaultFolder = store.getDefaultFolder();
            Folder[] remoteFolders = defaultFolder.list("*");

            for (Folder remote : remoteFolders) {
                if ((remote.getType() & Folder.HOLDS_MESSAGES) == 0) continue;

                String remoteName = remote.getFullName();
                // Skip junk/spam and trash during initial sync
                String lower = remoteName.toLowerCase();
                if (lower.contains("spam") || lower.contains("junk") || lower.contains("trash") || lower.contains("deleted")) {
                    continue;
                }

                // Find or create local folder
                MailFolder localFolder = folderMapper.selectOne(
                        new LambdaQueryWrapper<MailFolder>()
                                .eq(MailFolder::getUserId, userId)
                                .eq(MailFolder::getAccountId, accountId)
                                .eq(MailFolder::getRemoteName, remoteName)
                );
                if (localFolder == null) {
                    localFolder = new MailFolder();
                    localFolder.setUserId(userId);
                    localFolder.setAccountId(accountId);
                    localFolder.setName(remoteName);
                    localFolder.setRemoteName(remoteName);
                    localFolder.setType(inferFolderType(remoteName));
                    localFolder.setUnreadCount(0);
                    localFolder.setTotalCount(0);
                    folderMapper.insert(localFolder);
                }

                remote.open(Folder.READ_ONLY);
                Message[] msgs = remote.getMessages();

                for (Message msg : msgs) {
                    try {
                        String messageUid = String.valueOf(((UIDFolder) remote).getUID(msg));
                        // Skip if already synced
                        long exists = messageMapper.selectCount(
                                new LambdaQueryWrapper<MailMessage>()
                                        .eq(MailMessage::getAccountId, accountId)
                                        .eq(MailMessage::getMessageUid, messageUid)
                        );
                        if (exists > 0) continue;

                        MimeMessage mime = (MimeMessage) msg;
                        MailMessage entity = new MailMessage();
                        entity.setUserId(userId);
                        entity.setAccountId(accountId);
                        entity.setFolderId(localFolder.getId());
                        entity.setMessageUid(messageUid);
                        entity.setMessageId(mime.getMessageID());
                        entity.setSubject(mime.getSubject());
                        entity.setFromAddress(formatAddress(mime.getFrom()));
                        entity.setContentType("html");

                        Object content = mime.getContent();
                        if (content instanceof String str) {
                            entity.setContent(str);
                        } else if (content instanceof MimeMultipart mp) {
                            entity.setContent(extractText(mp));
                        }

                        Date sentDate = mime.getSentDate();
                        entity.setSentAt(sentDate != null ? sentDate.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime() : LocalDateTime.now());
                        Date recvDate = mime.getReceivedDate();
                        entity.setReceivedAt(recvDate != null ? recvDate.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime() : LocalDateTime.now());

                        Flags flags = mime.getFlags();
                        entity.setReadFlag(flags.contains(Flags.Flag.SEEN) ? 1 : 0);
                        entity.setStarFlag(flags.contains(Flags.Flag.FLAGGED) ? 1 : 0);
                        entity.setDraftFlag(flags.contains(Flags.Flag.DRAFT) ? 1 : 0);
                        entity.setDeletedFlag(0);

                        messageMapper.insert(entity);

                        // Save TO recipients
                        Address[] toAddr = mime.getRecipients(Message.RecipientType.TO);
                        if (toAddr != null) {
                            for (Address a : toAddr) {
                                MailRecipient r = new MailRecipient();
                                r.setMessageId(entity.getId());
                                r.setType("to");
                                r.setEmailAddress(((InternetAddress) a).getAddress());
                                r.setDisplayName(((InternetAddress) a).getPersonal());
                                recipientMapper.insert(r);
                            }
                        }

                    } catch (Exception e) {
                        // Skip problematic message and continue
                        System.err.println("Skip message: " + e.getMessage());
                    }
                }

                localFolder.setTotalCount(remote.getMessageCount());
                localFolder.setUnreadCount(remote.getUnreadMessageCount());
                folderMapper.updateById(localFolder);
                remote.close(false);
            }

            store.close();
            account.setLastSyncAt(LocalDateTime.now());
            accountMapper.updateById(account);

        } catch (Exception e) {
            throw new RuntimeException("IMAP 同步失败: " + e.getMessage(), e);
        }
    }

    private String inferFolderType(String name) {
        String lower = name.toLowerCase();
        if (lower.contains("inbox")) return "inbox";
        if (lower.contains("sent")) return "sent";
        if (lower.contains("draft")) return "draft";
        if (lower.contains("spam") || lower.contains("junk")) return "spam";
        if (lower.contains("trash") || lower.contains("deleted")) return "trash";
        return "custom";
    }

    private String formatAddress(Address[] addresses) {
        if (addresses == null || addresses.length == 0) return "";
        if (addresses[0] instanceof InternetAddress ia) {
            return ia.getAddress();
        }
        return addresses[0].toString();
    }

    private String extractText(MimeMultipart mp) {
        try {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < mp.getCount(); i++) {
                BodyPart bp = mp.getBodyPart(i);
                if (bp.isMimeType("text/plain") || bp.isMimeType("text/html")) {
                    sb.append(bp.getContent().toString());
                } else if (bp.getContent() instanceof MimeMultipart child) {
                    sb.append(extractText(child));
                }
            }
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }
}
