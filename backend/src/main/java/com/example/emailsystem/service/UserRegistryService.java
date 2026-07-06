package com.example.emailsystem.service;

import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.dto.AppDtos.RegisterRequest;
import com.example.emailsystem.security.AuthUser;
import jakarta.annotation.PostConstruct;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserRegistryService {
    private static final Logger log = LoggerFactory.getLogger(UserRegistryService.class);

    private final AtomicLong userIdGenerator = new AtomicLong(1);
    private final Map<String, StoredUser> usersByUsername = new ConcurrentHashMap<>();
    private final Map<Long, StoredUser> usersById = new ConcurrentHashMap<>();
    private final PasswordEncoder passwordEncoder;
    private final DemoMailboxService mailboxService;

    @Value("${app.initial-admin.password:}")
    private String initialAdminPassword;

    public UserRegistryService(PasswordEncoder passwordEncoder, DemoMailboxService mailboxService) {
        this.passwordEncoder = passwordEncoder;
        this.mailboxService = mailboxService;
    }

    @PostConstruct
    void initAdmin() {
        if (initialAdminPassword != null && !initialAdminPassword.isBlank()) {
            registerInitialAdmin();
        }
    }

    public AuthUser register(RegisterRequest request) {
        String username = normalizeUsername(request.username());
        String emailAddress = normalizeEmail(request.emailAddress());
        if (usersByUsername.containsKey(username)) {
            throw new BusinessException("AUTH_400", "用户名已存在");
        }
        if (mailboxService.emailAddressExists(emailAddress)) {
            throw new BusinessException("MAIL_400", "邮箱地址已被注册");
        }
        long userId = userIdGenerator.incrementAndGet();
        StoredUser user = new StoredUser(
            userId,
            username,
            passwordEncoder.encode(request.password()),
            request.displayName(),
            emailAddress
        );
        usersByUsername.put(username, user);
        usersById.put(userId, user);
        mailboxService.createDefaultMailbox(userId, emailAddress, request.displayName());
        return user.toAuthUser();
    }

    public AuthUser login(String username, String password) {
        StoredUser user = usersByUsername.get(normalizeUsername(username));
        if (user == null || !passwordEncoder.matches(password, user.passwordHash())) {
            throw new BusinessException("AUTH_401", "用户名或密码错误");
        }
        return user.toAuthUser();
    }

    public AuthUser getUser(Long userId) {
        StoredUser user = usersById.get(userId);
        if (user == null) {
            throw new BusinessException("AUTH_401", "用户不存在");
        }
        return user.toAuthUser();
    }

    private void registerInitialAdmin() {
        String username = "admin";
        String emailAddress = "admin@example.com";
        if (usersByUsername.containsKey(username)) {
            log.info("Initial admin user already exists, skipping creation");
            return;
        }
        StoredUser user = new StoredUser(
            1L,
            username,
            passwordEncoder.encode(initialAdminPassword),
            "Admin",
            emailAddress
        );
        usersByUsername.put(username, user);
        usersById.put(1L, user);
        log.info("Initial admin user created. Change the password immediately.");
    }

    private String normalizeUsername(String username) {
        return username == null ? "" : username.trim().toLowerCase();
    }

    private String normalizeEmail(String emailAddress) {
        return emailAddress == null ? "" : emailAddress.trim().toLowerCase();
    }

    private record StoredUser(
        Long id,
        String username,
        String passwordHash,
        String displayName,
        String emailAddress
    ) {
        AuthUser toAuthUser() {
            return new AuthUser(id, username, displayName);
        }
    }
}
