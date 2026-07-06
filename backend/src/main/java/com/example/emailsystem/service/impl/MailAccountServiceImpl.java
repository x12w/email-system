package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.dto.request.CreateMailAccountRequest;
import com.example.emailsystem.dto.request.UpdateMailAccountRequest;
import com.example.emailsystem.dto.response.MailAccountResponse;
import com.example.emailsystem.entity.MailAccount;
import com.example.emailsystem.mapper.MailAccountMapper;
import com.example.emailsystem.service.MailAccountService;
import com.example.emailsystem.util.AesEncryptUtil;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class MailAccountServiceImpl implements MailAccountService {

    private final MailAccountMapper mailAccountMapper;
    private final AesEncryptUtil encryptUtil;

    public MailAccountServiceImpl(MailAccountMapper mailAccountMapper, AesEncryptUtil encryptUtil) {
        this.mailAccountMapper = mailAccountMapper;
        this.encryptUtil = encryptUtil;
    }

    @Override
    public List<MailAccountResponse> listAccounts(Long userId) {
        return mailAccountMapper.selectList(
                new LambdaQueryWrapper<MailAccount>().eq(MailAccount::getUserId, userId)
        ).stream().map(MailAccountResponse::from).toList();
    }

    @Override
    public MailAccountResponse getAccount(Long userId, Long id) {
        MailAccount acct = mailAccountMapper.selectOne(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, id)
                        .eq(MailAccount::getUserId, userId)
        );
        if (acct == null) throw new IllegalArgumentException("邮箱账号不存在");
        return MailAccountResponse.from(acct);
    }

    @Override
    @Transactional
    public MailAccountResponse createAccount(Long userId, CreateMailAccountRequest req) {
        MailAccount acct = new MailAccount();
        acct.setUserId(userId);
        acct.setEmailAddress(req.emailAddress());
        acct.setDisplayName(req.displayName());
        acct.setSmtpHost(req.smtpHost());
        acct.setSmtpPort(req.smtpPort());
        acct.setSmtpSsl(req.smtpSsl() != null ? req.smtpSsl() : 0);
        acct.setImapHost(req.imapHost());
        acct.setImapPort(req.imapPort());
        acct.setImapSsl(req.imapSsl() != null ? req.imapSsl() : 0);
        acct.setAuthUsername(req.authUsername());
        acct.setAuthPasswordEncrypted(encryptUtil.encrypt(req.authPassword()));
        acct.setStatus(1);
        mailAccountMapper.insert(acct);
        return MailAccountResponse.from(acct);
    }

    @Override
    @Transactional
    public MailAccountResponse updateAccount(Long userId, Long id, UpdateMailAccountRequest req) {
        MailAccount acct = mailAccountMapper.selectOne(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, id)
                        .eq(MailAccount::getUserId, userId)
        );
        if (acct == null) throw new IllegalArgumentException("邮箱账号不存在");

        acct.setEmailAddress(req.emailAddress());
        acct.setDisplayName(req.displayName());
        acct.setSmtpHost(req.smtpHost());
        acct.setSmtpPort(req.smtpPort());
        acct.setSmtpSsl(req.smtpSsl() != null ? req.smtpSsl() : 0);
        acct.setImapHost(req.imapHost());
        acct.setImapPort(req.imapPort());
        acct.setImapSsl(req.imapSsl() != null ? req.imapSsl() : 0);
        acct.setAuthUsername(req.authUsername());
        if (req.authPassword() != null && !req.authPassword().isBlank()) {
            acct.setAuthPasswordEncrypted(encryptUtil.encrypt(req.authPassword()));
        }
        mailAccountMapper.updateById(acct);
        return MailAccountResponse.from(acct);
    }

    @Override
    @Transactional
    public void deleteAccount(Long userId, Long id) {
        int affected = mailAccountMapper.delete(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, id)
                        .eq(MailAccount::getUserId, userId)
        );
        if (affected == 0) throw new IllegalArgumentException("邮箱账号不存在");
    }

    @Override
    public void testConnection(Long userId, Long id) {
        MailAccount acct = mailAccountMapper.selectOne(
                new LambdaQueryWrapper<MailAccount>()
                        .eq(MailAccount::getId, id)
                        .eq(MailAccount::getUserId, userId)
        );
        if (acct == null) throw new IllegalArgumentException("邮箱账号不存在");
        // Connection test will be implemented with Jakarta Mail in Phase 3 SMTP
        throw new UnsupportedOperationException("连接测试将在发信模块完成后可用");
    }
}
