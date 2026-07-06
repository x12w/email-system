package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.MailFolder;
import com.example.emailsystem.mapper.MailFolderMapper;
import com.example.emailsystem.mapper.MailMessageMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class MailFolderService {
    private final MailFolderMapper mailFolderMapper;
    private final MailMessageMapper mailMessageMapper;

    public MailFolderService(MailFolderMapper mailFolderMapper, MailMessageMapper mailMessageMapper) {
        this.mailFolderMapper = mailFolderMapper;
        this.mailMessageMapper = mailMessageMapper;
    }

    public List<MailFolder> listFolders(Long userId) {
        List<MailFolder> folders = mailFolderMapper.selectList(
            new QueryWrapper<MailFolder>().eq("user_id", userId).orderByAsc("id"));
        // 实时计算每个文件夹的邮件数量
        for (MailFolder folder : folders) {
            long total = mailMessageMapper.selectCount(
                new QueryWrapper<com.example.emailsystem.entity.MailMessage>()
                    .eq("folder_id", folder.getId())
                    .eq("deleted_flag", 0));
            long unread = mailMessageMapper.selectCount(
                new QueryWrapper<com.example.emailsystem.entity.MailMessage>()
                    .eq("folder_id", folder.getId())
                    .eq("read_flag", 0)
                    .eq("deleted_flag", 0));
            folder.setTotalCount((int) total);
            folder.setUnreadCount((int) unread);
        }
        return folders;
    }

    public List<MailFolder> listFoldersByAccount(Long accountId) {
        return mailFolderMapper.selectList(
            new QueryWrapper<MailFolder>().eq("account_id", accountId).orderByAsc("id"));
    }

    public MailFolder getOrCreateInboxFolder(Long accountId, Long userId) {
        return getOrCreateFolder(accountId, userId, "inbox", "收件箱", "INBOX");
    }

    public MailFolder getOrCreateSentFolder(Long accountId, Long userId) {
        return getOrCreateFolder(accountId, userId, "sent", "已发送", "Sent");
    }

    public MailFolder getOrCreateDraftFolder(Long accountId, Long userId) {
        return getOrCreateFolder(accountId, userId, "draft", "草稿箱", "Drafts");
    }

    public MailFolder getOrCreateSpamFolder(Long accountId, Long userId) {
        return getOrCreateFolder(accountId, userId, "spam", "垃圾邮件", "Spam");
    }

    public MailFolder getOrCreateFolder(Long accountId, Long userId, String type, String name, String remoteName) {
        MailFolder folder = mailFolderMapper.selectOne(
            new QueryWrapper<MailFolder>()
                .eq("account_id", accountId)
                .eq("type", type));
        if (folder == null) {
            folder = new MailFolder();
            folder.setUserId(userId);
            folder.setAccountId(accountId);
            folder.setName(name);
            folder.setRemoteName(remoteName);
            folder.setType(type);
            folder.setUnreadCount(0);
            folder.setTotalCount(0);
            folder.setCreatedAt(LocalDateTime.now());
            folder.setUpdatedAt(LocalDateTime.now());
            mailFolderMapper.insert(folder);
        }
        return folder;
    }

    public MailFolder getFolder(Long folderId) {
        MailFolder folder = mailFolderMapper.selectById(folderId);
        if (folder == null) {
            throw new BusinessException("MAIL_400", "文件夹不存在");
        }
        return folder;
    }

    public void updateCounts(Long folderId, int unreadDelta, int totalDelta) {
        MailFolder folder = getFolder(folderId);
        folder.setUnreadCount(Math.max(0, folder.getUnreadCount() + unreadDelta));
        folder.setTotalCount(Math.max(0, folder.getTotalCount() + totalDelta));
        folder.setUpdatedAt(LocalDateTime.now());
        mailFolderMapper.updateById(folder);
    }

    public void createDefaultFolders(Long accountId, Long userId) {
        getOrCreateInboxFolder(accountId, userId);
        getOrCreateSentFolder(accountId, userId);
        getOrCreateDraftFolder(accountId, userId);
        getOrCreateSpamFolder(accountId, userId);
    }
}
