package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.emailsystem.dto.response.MessageResponse;
import com.example.emailsystem.entity.MailMessage;
import com.example.emailsystem.mapper.MailMessageMapper;
import com.example.emailsystem.service.MessageQueryService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class MessageQueryServiceImpl implements MessageQueryService {

    private final MailMessageMapper messageMapper;

    public MessageQueryServiceImpl(MailMessageMapper messageMapper) {
        this.messageMapper = messageMapper;
    }

    @Override
    public List<MessageResponse> listMessages(Long userId, Long folderId, String keyword, Boolean read, int page, int size) {
        LambdaQueryWrapper<MailMessage> qw = new LambdaQueryWrapper<MailMessage>()
                .eq(MailMessage::getUserId, userId)
                .eq(MailMessage::getDeletedFlag, 0);

        if (folderId != null) qw.eq(MailMessage::getFolderId, folderId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(MailMessage::getSubject, keyword)
                    .or().like(MailMessage::getContent, keyword));
        }
        if (read != null) qw.eq(MailMessage::getReadFlag, read ? 1 : 0);

        qw.orderByDesc(MailMessage::getReceivedAt);

        Page<MailMessage> p = messageMapper.selectPage(new Page<>(page, size), qw);
        return p.getRecords().stream().map(MessageResponse::from).toList();
    }

    @Override
    public MessageResponse getMessage(Long userId, Long id) {
        MailMessage msg = messageMapper.selectOne(
                new LambdaQueryWrapper<MailMessage>()
                        .eq(MailMessage::getId, id)
                        .eq(MailMessage::getUserId, userId)
                        .eq(MailMessage::getDeletedFlag, 0)
        );
        if (msg == null) throw new IllegalArgumentException("邮件不存在");
        return MessageResponse.from(msg);
    }

    @Override
    @Transactional
    public void markRead(Long userId, Long id, boolean read) {
        MailMessage msg = messageMapper.selectOne(
                new LambdaQueryWrapper<MailMessage>()
                        .eq(MailMessage::getId, id)
                        .eq(MailMessage::getUserId, userId)
        );
        if (msg == null) throw new IllegalArgumentException("邮件不存在");
        msg.setReadFlag(read ? 1 : 0);
        messageMapper.updateById(msg);
    }

    @Override
    @Transactional
    public void deleteMessage(Long userId, Long id) {
        MailMessage msg = messageMapper.selectOne(
                new LambdaQueryWrapper<MailMessage>()
                        .eq(MailMessage::getId, id)
                        .eq(MailMessage::getUserId, userId)
        );
        if (msg == null) throw new IllegalArgumentException("邮件不存在");
        msg.setDeletedFlag(1);
        messageMapper.updateById(msg);
    }

    @Override
    public long countTotal(Long userId, Long folderId, String keyword, Boolean read) {
        LambdaQueryWrapper<MailMessage> qw = new LambdaQueryWrapper<MailMessage>()
                .eq(MailMessage::getUserId, userId)
                .eq(MailMessage::getDeletedFlag, 0);

        if (folderId != null) qw.eq(MailMessage::getFolderId, folderId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(MailMessage::getSubject, keyword)
                    .or().like(MailMessage::getContent, keyword));
        }
        if (read != null) qw.eq(MailMessage::getReadFlag, read ? 1 : 0);

        return messageMapper.selectCount(qw);
    }
}
