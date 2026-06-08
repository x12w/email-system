package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.AppDtos.PluginStatusResponse;
import com.example.emailsystem.dto.AppDtos.PushEventResponse;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.example.emailsystem.intelligence.service.IntelligenceAnalysisService;
import com.example.emailsystem.service.DemoMailboxService;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/intelligence")
public class IntelligenceController {
    private final IntelligenceAnalysisService intelligenceAnalysisService;
    private final DemoMailboxService mailboxService;
    private final String pluginName;
    private final String pluginVersion;
    private final boolean pluginEnabled;
    private final int timeoutMs;

    public IntelligenceController(
        IntelligenceAnalysisService intelligenceAnalysisService,
        DemoMailboxService mailboxService,
        @Value("${intelligence.plugin.name}") String pluginName,
        @Value("${intelligence.plugin.version}") String pluginVersion,
        @Value("${intelligence.plugin.enabled}") boolean pluginEnabled,
        @Value("${intelligence.plugin.timeout-ms}") int timeoutMs
    ) {
        this.intelligenceAnalysisService = intelligenceAnalysisService;
        this.mailboxService = mailboxService;
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
        return ApiResponse.ok(mailboxService.listPushEvents().stream()
            .map(event -> new ThreatIndicator("message", String.valueOf(event.messageId()), event.priority(), event.content()))
            .toList());
    }

    @GetMapping("/push-events")
    public ApiResponse<List<PushEventResponse>> pushEvents() {
        return ApiResponse.ok(mailboxService.listPushEvents());
    }

    @PutMapping("/push-events/{id}/read")
    public ApiResponse<PushEventResponse> markPushEventRead(@PathVariable Long id) {
        return ApiResponse.ok(mailboxService.markPushEventRead(id));
    }

    @GetMapping("/plugins")
    public ApiResponse<List<PluginStatusResponse>> plugins() {
        return ApiResponse.ok(List.of(new PluginStatusResponse(
            pluginName, pluginVersion, "java-rule-fallback", pluginEnabled, timeoutMs, "ready"
        )));
    }
}
