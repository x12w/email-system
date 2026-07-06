package com.example.emailsystem.storage;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

@Service
public class LocalStorageService implements StorageService {

    private final Path rootPath;

    public LocalStorageService(@Value("${storage.local.root-path}") String rootPath) {
        this.rootPath = Paths.get(rootPath).toAbsolutePath().normalize();
    }

    @PostConstruct
    public void init() throws IOException {
        Files.createDirectories(rootPath);
    }

    @Override
    public String store(String prefix, byte[] data, String originalName, String contentType) {
        String dir = prefix != null ? prefix : "attachments";
        String fileName = UUID.randomUUID() + "_" + originalName;
        try {
            Path targetDir = rootPath.resolve(dir);
            Files.createDirectories(targetDir);
            Files.write(targetDir.resolve(fileName), data);
            return dir + "/" + fileName;
        } catch (IOException e) {
            throw new RuntimeException("Failed to store file", e);
        }
    }

    @Override
    public Resource loadAsResource(String storagePath) {
        Path file = rootPath.resolve(storagePath).normalize();
        if (!file.startsWith(rootPath)) {
            throw new SecurityException("Invalid storage path");
        }
        return new FileSystemResource(file);
    }

    @Override
    public void delete(String storagePath) {
        try {
            Path file = rootPath.resolve(storagePath).normalize();
            if (file.startsWith(rootPath)) {
                Files.deleteIfExists(file);
            }
        } catch (IOException e) {
            throw new RuntimeException("Failed to delete file", e);
        }
    }
}
