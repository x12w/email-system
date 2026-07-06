package com.example.emailsystem.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.dto.AppDtos.RegisterRequest;
import com.example.emailsystem.entity.SysUser;
import com.example.emailsystem.mapper.SysUserMapper;
import com.example.emailsystem.security.AuthUser;
import jakarta.annotation.PostConstruct;
import java.time.LocalDateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserRegistryService {
    private static final Logger log = LoggerFactory.getLogger(UserRegistryService.class);

    private final SysUserMapper sysUserMapper;
    private final PasswordEncoder passwordEncoder;
    private final MailAccountService mailAccountService;

    @Value("${app.initial-admin.password:}")
    private String initialAdminPassword;

    public UserRegistryService(PasswordEncoder passwordEncoder, MailAccountService mailAccountService,
                                SysUserMapper sysUserMapper) {
        this.passwordEncoder = passwordEncoder;
        this.mailAccountService = mailAccountService;
        this.sysUserMapper = sysUserMapper;
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

        if (sysUserMapper.selectCount(
            new QueryWrapper<SysUser>().eq("username", username)) > 0) {
            throw new BusinessException("AUTH_400", "用户名已存在");
        }

        SysUser user = new SysUser();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setDisplayName(request.displayName());
        user.setEmail(emailAddress);
        user.setStatus(1);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        sysUserMapper.insert(user);

        log.info("用户已注册: {} (id={})", username, user.getId());

        // Try to create a default mailbox; skip if email already used by this user
        try {
            mailAccountService.createDefaultMailbox(user.getId(), emailAddress, request.displayName());
        } catch (BusinessException ignored) {
            // Mailbox already exists for this user
        }
        return new AuthUser(user.getId(), user.getUsername(), user.getDisplayName());
    }

    public AuthUser login(String username, String password) {
        SysUser user = sysUserMapper.selectOne(
            new QueryWrapper<SysUser>().eq("username", normalizeUsername(username)));
        if (user == null || !passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new BusinessException("AUTH_401", "用户名或密码错误");
        }
        return new AuthUser(user.getId(), user.getUsername(), user.getDisplayName());
    }

    public AuthUser getUser(Long userId) {
        SysUser user = sysUserMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException("AUTH_401", "用户不存在");
        }
        return new AuthUser(user.getId(), user.getUsername(), user.getDisplayName());
    }

    private void registerInitialAdmin() {
        String username = "admin";
        if (sysUserMapper.selectCount(
            new QueryWrapper<SysUser>().eq("username", username)) > 0) {
            log.info("Initial admin user already exists");
            return;
        }
        SysUser user = new SysUser();
        user.setId(1L);
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(initialAdminPassword));
        user.setDisplayName("Admin");
        user.setEmail("admin@x12w.com");
        user.setStatus(1);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());
        sysUserMapper.insert(user);
        log.info("Initial admin user created");
    }

    private String normalizeUsername(String username) {
        return username == null ? "" : username.trim().toLowerCase();
    }

    private String normalizeEmail(String emailAddress) {
        return emailAddress == null ? "" : emailAddress.trim().toLowerCase();
    }
}
