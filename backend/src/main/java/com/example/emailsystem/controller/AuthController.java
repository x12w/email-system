package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.dto.AppDtos.LoginRequest;
import com.example.emailsystem.dto.AppDtos.LoginResponse;
import com.example.emailsystem.dto.AppDtos.UserInfo;
import com.example.emailsystem.security.AuthUser;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.security.TokenService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private final TokenService tokenService;

    public AuthController(TokenService tokenService) {
        this.tokenService = tokenService;
    }

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        if (!"admin".equals(request.username()) || !"password".equals(request.password())) {
            throw new BusinessException("AUTH_401", "用户名或密码错误");
        }
        AuthUser authUser = new AuthUser(1L, "admin", "Admin");
        return ApiResponse.ok(new LoginResponse(
            tokenService.createAccessToken(authUser),
            tokenService.createRefreshToken(authUser),
            tokenService.expireSeconds(),
            new UserInfo(authUser.id(), authUser.username(), authUser.displayName())
        ));
    }

    @PostMapping("/refresh")
    public ApiResponse<LoginResponse> refresh(@RequestBody(required = false) String ignored) {
        AuthUser authUser = new AuthUser(1L, "admin", "Admin");
        return ApiResponse.ok(new LoginResponse(
            tokenService.createAccessToken(authUser),
            tokenService.createRefreshToken(authUser),
            tokenService.expireSeconds(),
            new UserInfo(authUser.id(), authUser.username(), authUser.displayName())
        ));
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout() {
        return ApiResponse.ok(null);
    }

    @GetMapping("/me")
    public ApiResponse<UserInfo> me() {
        AuthUser user = SecurityUtils.currentUser();
        return ApiResponse.ok(new UserInfo(user.id(), user.username(), user.displayName()));
    }
}
