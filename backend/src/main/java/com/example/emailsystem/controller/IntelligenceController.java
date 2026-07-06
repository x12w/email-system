package com.example.emailsystem.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.PluginStatusResponse;
import com.example.emailsystem.dto.AppDtos.PushEventResponse;
import com.example.emailsystem.entity.MailPushEvent;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.example.emailsystem.intelligence.service.IntelligenceAnalysisService;
import com.example.emailsystem.mapper.MailPushEventMapper;
import com.example.emailsystem.security.SecurityUtils;
import java.time.ZoneId;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/intelligence")
public class IntelligenceController {
    private final IntelligenceAnalysisService intelligenceAnalysisService;
    private final MailPushEventMapper mailPushEventMapper;
    private final String pluginName;
    private final String pluginVersion;
    private final boolean pluginEnabled;
    private final int timeoutMs;

    public IntelligenceController(
        IntelligenceAnalysisService intelligenceAnalysisService,
        MailPushEventMapper mailPushEventMapper,
        @Value("${intelligence.plugin.name}") String pluginName,
        @Value("${intelligence.plugin.version}") String pluginVersion,
        @Value("${intelligence.plugin.enabled}") boolean pluginEnabled,
        @Value("${intelligence.plugin.timeout-ms}") int timeoutMs
    ) {
        this.intelligenceAnalysisService = intelligenceAnalysisService;
        this.mailPushEventMapper = mailPushEventMapper;
        this.pluginName = pluginName;
        this.pluginVersion = pluginVersion;
        this.pluginEnabled = pluginEnabled;
        this.timeoutMs = timeoutMs;
    }

    @GetMapping("/messages/{messageId}")
    public ApiResponse<IntelligenceAnalysisResult> getMessageResult(@PathVariable Long messageId) {
        return ApiResponse.ok(intelligenceAnalysisService.getMessageResult(messageId));
    }

    @PostMapping("/messages/{messageId}/analyze")
    public ApiResponse<IntelligenceAnalysisResult> analyzeMessage(@PathVariable Long messageId) {
        return ApiResponse.ok(intelligenceAnalysisService.analyzeMessage(messageId));
    }

    @GetMapping("/threats")
    public ApiResponse<List<ThreatIndicator>> threats() {
        List<MailPushEvent> events = mailPushEventMapper.selectList(
            new QueryWrapper<MailPushEvent>()
                .eq("user_id", SecurityUtils.currentUser().id())
                .orderByDesc("created_at"));
        return ApiResponse.ok(events.stream()
            .map(e -> new ThreatIndicator(e.getEventType(), String.valueOf(e.getMessageId()),
                e.getPriority(), e.getContent()))
            .collect(Collectors.toList()));
    }

    @GetMapping("/push-events")
    public ApiResponse<List<PushEventResponse>> pushEvents() {
        List<MailPushEvent> events = mailPushEventMapper.selectList(
            new QueryWrapper<MailPushEvent>()
                .eq("user_id", SecurityUtils.currentUser().id())
                .orderByDesc("created_at"));
        return ApiResponse.ok(events.stream().map(this::toPushEvent).collect(Collectors.toList()));
    }

    @PutMapping("/push-events/{id}/read")
    public ApiResponse<PushEventResponse> markPushEventRead(@PathVariable Long id) {
        MailPushEvent event = mailPushEventMapper.selectById(id);
        if (event != null) {
            event.setReadFlag(1);
            mailPushEventMapper.updateById(event);
        }
        return ApiResponse.ok(toPushEvent(event));
    }

    @GetMapping("/plugins")
    public ApiResponse<List<PluginStatusResponse>> plugins() {
        return ApiResponse.ok(List.of(new PluginStatusResponse(
            pluginName, pluginVersion, "java-rule-fallback", pluginEnabled, timeoutMs, "ready")));
    }

    private PushEventResponse toPushEvent(MailPushEvent e) {
        if (e == null) return null;
        return new PushEventResponse(e.getId(), e.getMessageId(), e.getEventType(), e.getTitle(),
            e.getContent(), e.getPriority(), e.getReadFlag() == 1,
            e.getPushedAt() != null ? e.getPushedAt().atZone(ZoneId.systemDefault()).toOffsetDateTime() : null);
    }
}
