package com.example.emailsystem.controller;

import com.example.emailsystem.common.ApiResponse;
import com.example.emailsystem.dto.response.PageResult;
import com.example.emailsystem.entity.MailPushEvent;
import com.example.emailsystem.entity.MailThreatIndicator;
import com.example.emailsystem.intelligence.dto.IntelligenceAnalysisResult;
import com.example.emailsystem.intelligence.dto.ThreatIndicator;
import com.example.emailsystem.intelligence.service.IntelligenceAnalysisService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.emailsystem.mapper.MailPushEventMapper;
import com.example.emailsystem.mapper.MailThreatIndicatorMapper;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/intelligence")
public class IntelligenceController {

    private final IntelligenceAnalysisService analysisService;
    private final MailThreatIndicatorMapper threatIndicatorMapper;
    private final MailPushEventMapper pushEventMapper;

    public IntelligenceController(IntelligenceAnalysisService analysisService,
                                  MailThreatIndicatorMapper threatIndicatorMapper,
                                  MailPushEventMapper pushEventMapper) {
        this.analysisService = analysisService;
        this.threatIndicatorMapper = threatIndicatorMapper;
        this.pushEventMapper = pushEventMapper;
    }

    @GetMapping("/messages/{messageId}")
    public ApiResponse<IntelligenceAnalysisResult> getResult(Authentication auth, @PathVariable Long messageId) {
        Long userId = (Long) auth.getPrincipal();
        IntelligenceAnalysisResult result = analysisService.getMessageResult(messageId);
        return ApiResponse.ok(result);
    }

    @PostMapping("/messages/{messageId}/analyze")
    public ApiResponse<IntelligenceAnalysisResult> analyze(Authentication auth, @PathVariable Long messageId) {
        Long userId = (Long) auth.getPrincipal();
        IntelligenceAnalysisResult result = analysisService.analyzeMessage(messageId);
        return ApiResponse.ok(result);
    }

    @GetMapping("/threats")
    public ApiResponse<List<ThreatIndicatorResponse>> listThreats(Authentication auth,
                                                                   @RequestParam(defaultValue = "1") int page,
                                                                   @RequestParam(defaultValue = "20") int size) {
        Long userId = (Long) auth.getPrincipal();
        var threats = threatIndicatorMapper.selectList(
                new LambdaQueryWrapper<MailThreatIndicator>()
                        .eq(MailThreatIndicator::getUserId, userId)
                        .orderByDesc(MailThreatIndicator::getId)
        );
        var responses = threats.stream().map(t -> new ThreatIndicatorResponse(
                t.getId(), t.getMessageId(), t.getType(), t.getValue(),
                t.getRiskLevel(), t.getReason(), t.getCreatedAt()
        )).toList();
        return ApiResponse.ok(responses);
    }

    @GetMapping("/push-events")
    public ApiResponse<List<PushEventResponse>> listPushEvents(Authentication auth) {
        Long userId = (Long) auth.getPrincipal();
        var events = pushEventMapper.selectList(
                new LambdaQueryWrapper<MailPushEvent>()
                        .eq(MailPushEvent::getUserId, userId)
                        .orderByDesc(MailPushEvent::getPushedAt)
        );
        var responses = events.stream().map(e -> new PushEventResponse(
                e.getId(), e.getMessageId(), e.getEventType(), e.getTitle(),
                e.getContent(), e.getPriority(), e.getReadFlag(), e.getPushedAt()
        )).toList();
        return ApiResponse.ok(responses);
    }

    @PutMapping("/push-events/{id}/read")
    public ApiResponse<Void> markPushRead(Authentication auth, @PathVariable Long id) {
        Long userId = (Long) auth.getPrincipal();
        MailPushEvent event = pushEventMapper.selectOne(
                new LambdaQueryWrapper<MailPushEvent>()
                        .eq(MailPushEvent::getId, id)
                        .eq(MailPushEvent::getUserId, userId)
        );
        if (event == null) throw new IllegalArgumentException("推送事件不存在");
        event.setReadFlag(1);
        pushEventMapper.updateById(event);
        return ApiResponse.ok(null);
    }

    // Response records
    public record ThreatIndicatorResponse(Long id, Long messageId, String type, String value,
                                          String riskLevel, String reason, java.time.LocalDateTime createdAt) {}

    public record PushEventResponse(Long id, Long messageId, String eventType, String title,
                                    String content, String priority, Integer readFlag,
                                    java.time.LocalDateTime pushedAt) {}
}
