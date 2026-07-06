package com.example.emailsystem.service;

import com.example.emailsystem.dto.response.AttachmentResponse;
import org.springframework.core.io.Resource;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface AttachmentService {
    AttachmentResponse upload(Long userId, MultipartFile file);
    Resource download(Long userId, Long id);
    void delete(Long userId, Long id);
    List<AttachmentResponse> getAttachmentsByMessageId(Long messageId);
}
