package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.common.PageResult;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.entity.MailRecipient;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.mapper.MailRecipientMapper;
import com.example.emailsystem.service.MailMessageService;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MailMessageServiceImpl extends ServiceImpl<MailMessageMapper, MailMessage> implements MailMessageService {
    private static final Logger log = LoggerFactory.getLogger(MailMessageServiceImpl.class);

    private final MailRecipientMapper mailRecipientMapper;

    public MailMessageServiceImpl(MailRecipientMapper mailRecipientMapper) {
        this.mailRecipientMapper = mailRecipientMapper;
    }

    @Override
    public void receiveAndProcessEmail(MailMessage message) {
        log.info("收到新邮件 from={} subject={}", message.getFromAddress(), message.getSubject());
        baseMapper.insert(message);
        log.info("邮件已存入数据库 id={}", message.getId());
    }

    public PageResult<MailMessage> listMessages(Long userId, Long folderId, String keyword,
                                                 Boolean read, List<Long> accountIds,
                                                 int page, int size) {
        QueryWrapper<MailMessage> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("deleted_flag", 0);
        if (folderId != null) {
            wrapper.eq("folder_id", folderId);
        }
        if (accountIds != null && !accountIds.isEmpty()) {
            wrapper.in("account_id", accountIds);
        }
        if (read != null) {
            wrapper.eq("read_flag", read ? 1 : 0);
        }
        if (keyword != null && !keyword.isBlank()) {
            wrapper.and(w -> w.like("subject", keyword)
                .or().like("from_address", keyword)
                .or().like("preview", keyword));
        }
        wrapper.orderByDesc("received_at");

        Page<MailMessage> mpPage = new Page<>(page, size);
        Page<MailMessage> result = baseMapper.selectPage(mpPage, wrapper);
        return new PageResult<>(result.getRecords(), result.getCurrent(),
            result.getSize(), result.getTotal());
    }

    public MailMessage getMessage(Long userId, Long id) {
        MailMessage message = baseMapper.selectById(id);
        if (message == null || !message.getUserId().equals(userId)) {
            throw new BusinessException("MAIL_400", "邮件不存在");
        }
        return message;
    }

    public List<MailRecipient> getRecipients(Long messageId) {
        return mailRecipientMapper.selectList(
            new QueryWrapper<MailRecipient>().eq("message_id", messageId));
    }

    public void markRead(Long userId, Long id, boolean read) {
        MailMessage message = getMessage(userId, id);
        message.setReadFlag(read ? 1 : 0);
        baseMapper.updateById(message);
    }

    public void softDelete(Long userId, Long id) {
        MailMessage message = getMessage(userId, id);
        message.setDeletedFlag(1);
        baseMapper.updateById(message);
    }
}
