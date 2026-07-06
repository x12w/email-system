package com.example.emailsystem.service;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.entity.MailAttachment;
import com.example.emailsystem.mapper.MailAttachmentMapper;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
public class AttachmentService {
    private final MailAttachmentMapper mailAttachmentMapper;

    public AttachmentService(MailAttachmentMapper mailAttachmentMapper) {
        this.mailAttachmentMapper = mailAttachmentMapper;
    }

    public MailAttachment upload(Long userId, MultipartFile file) {
        MailAttachment attachment = new MailAttachment();
        attachment.setUserId(userId);
        attachment.setOriginalName(file.getOriginalFilename() == null ? "attachment" : file.getOriginalFilename());
        attachment.setContentType(file.getContentType());
        attachment.setSizeBytes(file.getSize());
        attachment.setStorageType("local");
        attachment.setStoragePath("/api/attachments/download");
        attachment.setCreatedAt(LocalDateTime.now());
        mailAttachmentMapper.insert(attachment);
        return attachment;
    }

    public MailAttachment getAttachment(Long id) {
        MailAttachment attachment = mailAttachmentMapper.selectById(id);
        if (attachment == null) {
            throw new BusinessException("STORAGE_500", "附件不存在");
        }
        return attachment;
    }

    public byte[] download(Long id) {
        MailAttachment attachment = getAttachment(id);
        return ("Demo attachment: " + attachment.getOriginalName()).getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }

    public void delete(Long id) {
        getAttachment(id);
        mailAttachmentMapper.deleteById(id);
    }
}
