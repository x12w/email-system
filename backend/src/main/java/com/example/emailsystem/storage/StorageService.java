package com.example.emailsystem.storage;

import org.springframework.core.io.Resource;

public interface StorageService {
    String store(String prefix, byte[] data, String originalName, String contentType);
    Resource loadAsResource(String storagePath);
    void delete(String storagePath);
}
