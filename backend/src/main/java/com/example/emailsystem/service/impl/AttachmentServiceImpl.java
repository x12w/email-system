package com.example.emailsystem.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.dto.response.AttachmentResponse;
import com.example.emailsystem.entity.MailAttachment;
import com.example.emailsystem.mapper.MailAttachmentMapper;
import com.example.emailsystem.service.AttachmentService;
import com.example.emailsystem.storage.StorageService;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@Service
public class AttachmentServiceImpl implements AttachmentService {

    private final MailAttachmentMapper attachmentMapper;
    private final StorageService storageService;

    public AttachmentServiceImpl(MailAttachmentMapper attachmentMapper, StorageService storageService) {
        this.attachmentMapper = attachmentMapper;
        this.storageService = storageService;
    }

    @Override
    @Transactional
    public AttachmentResponse upload(Long userId, MultipartFile file) {
        try {
            String storagePath = storageService.store("attachments", file.getBytes(),
                    file.getOriginalFilename(), file.getContentType());

            MailAttachment att = new MailAttachment();
            att.setUserId(userId);
            att.setOriginalName(file.getOriginalFilename());
            att.setContentType(file.getContentType());
            att.setSizeBytes(file.getSize());
            att.setStorageType("local");
            att.setStoragePath(storagePath);
            attachmentMapper.insert(att);
            return AttachmentResponse.from(att);
        } catch (IOException e) {
            throw new RuntimeException("Failed to upload attachment", e);
        }
    }

    @Override
    public Resource download(Long userId, Long id) {
        MailAttachment att = attachmentMapper.selectOne(
                new LambdaQueryWrapper<MailAttachment>()
                        .eq(MailAttachment::getId, id)
                        .eq(MailAttachment::getUserId, userId)
        );
        if (att == null) throw new IllegalArgumentException("附件不存在");
        return storageService.loadAsResource(att.getStoragePath());
    }

    @Override
    @Transactional
    public void delete(Long userId, Long id) {
        MailAttachment att = attachmentMapper.selectOne(
                new LambdaQueryWrapper<MailAttachment>()
                        .eq(MailAttachment::getId, id)
                        .eq(MailAttachment::getUserId, userId)
        );
        if (att == null) throw new IllegalArgumentException("附件不存在");
        storageService.delete(att.getStoragePath());
        attachmentMapper.deleteById(id);
    }

    @Override
    public List<AttachmentResponse> getAttachmentsByMessageId(Long messageId) {
        return attachmentMapper.selectList(
                new LambdaQueryWrapper<MailAttachment>().eq(MailAttachment::getMessageId, messageId)
        ).stream().map(AttachmentResponse::from).toList();
    }
}
