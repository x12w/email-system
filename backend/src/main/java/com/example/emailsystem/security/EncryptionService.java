package com.example.emailsystem.security;

import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * AES-256-GCM encryption for sensitive stored fields (IMAP/SMTP passwords).
 * Uses the JWT secret as the key derivation source so no additional secret is needed.
 */
@Service
public class EncryptionService {
    private static final Logger log = LoggerFactory.getLogger(EncryptionService.class);
    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final int GCM_IV_LEN = 12;
    private static final int GCM_TAG_LEN = 128;
    private static final int KEY_MIN_LENGTH = 16;

    private final String secret;
    private SecretKeySpec secretKey;

    public EncryptionService(@Value("${security.jwt.secret}") String secret) {
        this.secret = secret;
    }

    @PostConstruct
    void init() {
        // Derive a 32-byte AES-256 key from the JWT secret
        byte[] keyBytes = new byte[32];
        byte[] secretBytes = secret.getBytes(StandardCharsets.UTF_8);
        int copyLen = Math.min(secretBytes.length, 32);
        System.arraycopy(secretBytes, 0, keyBytes, 0, copyLen);
        // If secret is shorter than 32 bytes, pad with zeroes (validated elsewhere)
        this.secretKey = new SecretKeySpec(keyBytes, ALGORITHM);
    }

    /**
     * Encrypt plaintext. Returns base64-encoded ciphertext (IV prepended).
     */
    public String encrypt(String plaintext) {
        if (plaintext == null || plaintext.isEmpty()) {
            return plaintext;
        }
        try {
            byte[] iv = new byte[GCM_IV_LEN];
            new SecureRandom().nextBytes(iv);
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.ENCRYPT_MODE, secretKey, new GCMParameterSpec(GCM_TAG_LEN, iv));
            byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));
            byte[] combined = new byte[iv.length + ciphertext.length];
            System.arraycopy(iv, 0, combined, 0, iv.length);
            System.arraycopy(ciphertext, 0, combined, iv.length, ciphertext.length);
            return Base64.getEncoder().encodeToString(combined);
        } catch (Exception e) {
            log.error("Encryption failed", e);
            throw new IllegalStateException("Failed to encrypt sensitive data", e);
        }
    }

    /**
     * Decrypt ciphertext (base64-encoded, IV prepended).
     * Returns the original plaintext, or the input unchanged if it looks unencrypted
     * (handles legacy plaintext passwords and empty values).
     */
    public String decrypt(String ciphertext) {
        if (ciphertext == null || ciphertext.isEmpty()) {
            return ciphertext;
        }
        try {
            byte[] combined = Base64.getDecoder().decode(ciphertext);
            if (combined.length < GCM_IV_LEN + 1) {
                // Too short to be encrypted — return as-is (legacy plaintext)
                return ciphertext;
            }
            byte[] iv = new byte[GCM_IV_LEN];
            byte[] encrypted = new byte[combined.length - GCM_IV_LEN];
            System.arraycopy(combined, 0, iv, 0, GCM_IV_LEN);
            System.arraycopy(combined, GCM_IV_LEN, encrypted, 0, encrypted.length);
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            cipher.init(Cipher.DECRYPT_MODE, secretKey, new GCMParameterSpec(GCM_TAG_LEN, iv));
            return new String(cipher.doFinal(encrypted), StandardCharsets.UTF_8);
        } catch (Exception e) {
            // Decryption failed — likely legacy plaintext, return as-is
            log.debug("Decryption failed, treating as plaintext: {}", e.getMessage());
            return ciphertext;
        }
    }
}
