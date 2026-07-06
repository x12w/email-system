package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.LoginRequest;
import com.example.emailsystem.dto.LoginResponse;
import com.example.emailsystem.dto.RegisterRequest;
import com.example.emailsystem.entity.SysUser;
import com.example.emailsystem.mapper.SysUserMapper;
import com.example.emailsystem.security.JwtUtil;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.Authentication;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final SysUserMapper userMapper;
    private final JwtUtil jwtUtil;
    private final PasswordEncoder passwordEncoder;
    private final long expireSeconds;

    public AuthController(SysUserMapper userMapper,
                          JwtUtil jwtUtil,
                          PasswordEncoder passwordEncoder,
                          @Value("${security.jwt.expire-seconds}") long expireSeconds) {
        this.userMapper = userMapper;
        this.jwtUtil = jwtUtil;
        this.passwordEncoder = passwordEncoder;
        this.expireSeconds = expireSeconds;
    }

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest req, HttpServletRequest httpReq) {
        SysUser user = userMapper.selectOne(
                com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        .lambdaQuery(SysUser.class)
                        .eq(SysUser::getUsername, req.username())
        );
        if (user == null || !passwordEncoder.matches(req.password(), user.getPasswordHash())) {
            return ApiResponse.fail("AUTH_401", "用户名或密码错误");
        }

        String token = jwtUtil.generate(user.getId(), user.getUsername());
        var userInfo = new LoginResponse.UserInfo(user.getId(), user.getUsername(), user.getDisplayName());
        return ApiResponse.ok(new LoginResponse(token, expireSeconds, userInfo));
    }

    @PostMapping("/register")
    @Transactional
    public ApiResponse<LoginResponse> register(@Valid @RequestBody RegisterRequest req, HttpServletRequest httpReq) {
        long count = userMapper.selectCount(
                com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        .lambdaQuery(SysUser.class)
                        .eq(SysUser::getUsername, req.username())
        );
        if (count > 0) {
            return ApiResponse.fail("VALIDATION_400", "用户名已存在");
        }

        SysUser user = new SysUser();
        user.setUsername(req.username());
        user.setPasswordHash(passwordEncoder.encode(req.password()));
        user.setDisplayName(req.displayName());
        user.setStatus(1);
        userMapper.insert(user);

        String token = jwtUtil.generate(user.getId(), user.getUsername());
        var userInfo = new LoginResponse.UserInfo(user.getId(), user.getUsername(), user.getDisplayName());
        return ApiResponse.ok(new LoginResponse(token, expireSeconds, userInfo));
    }

    @GetMapping("/me")
    public ApiResponse<LoginResponse.UserInfo> me(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        SysUser user = userMapper.selectById(userId);
        if (user == null) {
            return ApiResponse.fail("AUTH_401", "用户不存在");
        }
        return ApiResponse.ok(new LoginResponse.UserInfo(user.getId(), user.getUsername(), user.getDisplayName()));
    }
}
