package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.mapper.MailAccountMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MailAccountService {
    private static final Logger log = LoggerFactory.getLogger(MailAccountService.class);

    private final MailAccountMapper mailAccountMapper;
    private final MailFolderService mailFolderService;

    public MailAccountService(MailAccountMapper mailAccountMapper, MailFolderService mailFolderService) {
        this.mailAccountMapper = mailAccountMapper;
        this.mailFolderService = mailFolderService;
    }

    public List<MailAccount> listAccounts(Long userId) {
        return mailAccountMapper.selectList(
            new QueryWrapper<MailAccount>().eq("user_id", userId));
    }

    public MailAccount getAccount(Long id) {
        MailAccount account = mailAccountMapper.selectById(id);
        if (account == null) {
            throw new BusinessException("MAIL_400", "邮箱账号不存在");
        }
        return account;
    }

    public MailAccount requireAccount(Long userId, Long id) {
        MailAccount account = getAccount(id);
        if (!account.getUserId().equals(userId)) {
            throw new BusinessException("AUTH_403", "无权限");
        }
        return account;
    }

    public boolean emailAddressExists(String emailAddress) {
        String normalized = emailAddress == null ? "" : emailAddress.trim().toLowerCase();
        return mailAccountMapper.selectCount(
            new QueryWrapper<MailAccount>().eq("email_address", normalized)) > 0;
    }

    public MailAccount createAccount(Long userId, MailAccount account) {
        String normalizedEmail = account.getEmailAddress().trim().toLowerCase();
        if (emailAddressExists(normalizedEmail)) {
            throw new BusinessException("MAIL_400", "邮箱地址已被注册");
        }
        account.setUserId(userId);
        account.setEmailAddress(normalizedEmail);
        account.setStatus(1);
        account.setCreatedAt(LocalDateTime.now());
        account.setUpdatedAt(LocalDateTime.now());
        mailAccountMapper.insert(account);
        mailFolderService.createDefaultFolders(account.getId(), userId);
        log.info("邮箱账号已创建: {} (userId={})", normalizedEmail, userId);
        return account;
    }

    public MailAccount updateAccount(Long userId, Long id, MailAccount update) {
        MailAccount account = requireAccount(userId, id);
        account.setEmailAddress(update.getEmailAddress().trim().toLowerCase());
        account.setDisplayName(update.getDisplayName());
        account.setSmtpHost(update.getSmtpHost());
        account.setSmtpPort(update.getSmtpPort());
        account.setSmtpSsl(update.getSmtpSsl());
        account.setImapHost(update.getImapHost());
        account.setImapPort(update.getImapPort());
        account.setImapSsl(update.getImapSsl());
        account.setAuthUsername(update.getAuthUsername());
        if (update.getAuthPasswordEncrypted() != null && !update.getAuthPasswordEncrypted().isBlank()) {
            account.setAuthPasswordEncrypted(update.getAuthPasswordEncrypted());
        }
        account.setUpdatedAt(LocalDateTime.now());
        mailAccountMapper.updateById(account);
        return account;
    }

    public void deleteAccount(Long userId, Long id) {
        requireAccount(userId, id);
        mailAccountMapper.deleteById(id);
    }

    public MailAccount createDefaultMailbox(Long userId, String emailAddress, String displayName) {
        MailAccount account = new MailAccount();
        account.setEmailAddress(emailAddress);
        account.setDisplayName(displayName);
        account.setSmtpHost("localhost");
        account.setSmtpPort(1025);
        account.setSmtpSsl(0);
        account.setImapHost("localhost");
        account.setImapPort(1143);
        account.setImapSsl(0);
        account.setAuthUsername(emailAddress);
        account.setAuthPasswordEncrypted("password");
        return createAccount(userId, account);
    }
}
