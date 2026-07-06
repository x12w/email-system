package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.common.BusinessException;
import com.example.emailsystem.dto.AppDtos.LoginRequest;
import com.example.emailsystem.dto.AppDtos.LoginResponse;
import com.example.emailsystem.dto.AppDtos.RefreshRequest;
import com.example.emailsystem.dto.AppDtos.RegisterRequest;
import com.example.emailsystem.dto.AppDtos.UserInfo;
import com.example.emailsystem.security.AuthUser;
import com.example.emailsystem.security.SecurityUtils;
import com.example.emailsystem.security.TokenService;
import com.example.emailsystem.service.UserRegistryService;
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
    private final UserRegistryService userRegistryService;

    public AuthController(TokenService tokenService, UserRegistryService userRegistryService) {
        this.tokenService = tokenService;
        this.userRegistryService = userRegistryService;
    }

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        return ApiResponse.ok(createSession(userRegistryService.login(request.username(), request.password())));
    }

    @PostMapping("/register")
    public ApiResponse<LoginResponse> register(@Valid @RequestBody RegisterRequest request) {
        return ApiResponse.ok(createSession(userRegistryService.register(request)));
    }

    @PostMapping("/refresh")
    public ApiResponse<LoginResponse> refresh(@RequestBody RefreshRequest request) {
        AuthUser authUser = tokenService.parse(request.refreshToken());
        if (authUser == null) {
            throw new BusinessException("AUTH_401", "refresh token 无效或已过期");
        }
        return ApiResponse.ok(createSession(userRegistryService.getUser(authUser.id())));
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

    private LoginResponse createSession(AuthUser authUser) {
        return new LoginResponse(
            tokenService.createAccessToken(authUser),
            tokenService.createRefreshToken(authUser),
            tokenService.expireSeconds(),
            new UserInfo(authUser.id(), authUser.username(), authUser.displayName())
        );
    }
}
