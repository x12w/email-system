package com.example.emailsystem.config;

import com.example.emailsystem.common.ApiResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class RateLimitFilter extends OncePerRequestFilter {
    private static final Logger log = LoggerFactory.getLogger(RateLimitFilter.class);

    private final int maxAttempts;
    private final long windowSeconds;
    private final ObjectMapper objectMapper;
    private final Map<String, RateWindow> attemptsByIp = new ConcurrentHashMap<>();

    public RateLimitFilter(
        @Value("${app.auth-rate-limit.max-attempts:5}") int maxAttempts,
        @Value("${app.auth-rate-limit.window-seconds:60}") long windowSeconds,
        ObjectMapper objectMapper
    ) {
        this.maxAttempts = maxAttempts;
        this.windowSeconds = windowSeconds;
        this.objectMapper = objectMapper;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
        String path = request.getRequestURI();
        if (!path.endsWith("/login") && !path.endsWith("/register")) {
            filterChain.doFilter(request, response);
            return;
        }
        if (!"POST".equalsIgnoreCase(request.getMethod())) {
            filterChain.doFilter(request, response);
            return;
        }

        String clientIp = getClientIp(request);
        RateWindow window = attemptsByIp.compute(clientIp, (key, current) -> {
            long now = System.currentTimeMillis();
            long windowStart = now - windowSeconds * 1000;
            if (current == null || current.windowStart() < windowStart) {
                return new RateWindow(now, 1);
            }
            return new RateWindow(current.windowStart(), current.count() + 1);
        });

        if (window.count() > maxAttempts) {
            log.warn("Rate limit exceeded for IP {} on {}", clientIp, path);
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.setContentType("application/json;charset=UTF-8");
            objectMapper.writeValue(response.getWriter(),
                ApiResponse.fail("RATE_429", "请求过于频繁，请稍后再试"));
            return;
        }

        filterChain.doFilter(request, response);
    }

    private String getClientIp(HttpServletRequest request) {
        String forwarded = request.getHeader("X-Forwarded-For");
        if (forwarded != null && !forwarded.isBlank()) {
            return forwarded.split(",")[0].trim();
        }
        String realIp = request.getHeader("X-Real-IP");
        if (realIp != null && !realIp.isBlank()) {
            return realIp.trim();
        }
        return request.getRemoteAddr();
    }

    private record RateWindow(long windowStart, int count) {
    }
}
