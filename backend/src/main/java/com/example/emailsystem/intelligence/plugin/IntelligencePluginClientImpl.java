package com.example.emailsystem.intelligence.plugin;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
public class IntelligencePluginClientImpl implements IntelligencePluginClient {

    private static final Logger log = LoggerFactory.getLogger(IntelligencePluginClientImpl.class);

    private final boolean enabled;
    private final String pythonCommand;
    private final String pluginEntry;
    private final long timeoutMs;
    private final ObjectMapper objectMapper;

    public IntelligencePluginClientImpl(
            @Value("${intelligence.plugin.enabled:true}") boolean enabled,
            @Value("${intelligence.plugin.python-command:python3}") String pythonCommand,
            @Value("${intelligence.plugin.entry:plugins/intelligence/python/src/plugin_entry.py}") String pluginEntry,
            @Value("${intelligence.plugin.timeout-ms:10000}") long timeoutMs,
            ObjectMapper objectMapper) {
        this.enabled = enabled;
        this.pythonCommand = pythonCommand;
        this.pluginEntry = pluginEntry;
        this.timeoutMs = timeoutMs;
        this.objectMapper = objectMapper;
    }

    @Override
    public String analyzeEmailJson(String requestJson) {
        if (!enabled) {
            return buildFallbackResult("插件未启用");
        }

        try {
            ProcessBuilder pb = new ProcessBuilder(
                    pythonCommand, "-c",
                    "import sys; sys.path.insert(0, '.'); from src.plugin_entry import analyze_email_json; print(analyze_email_json(sys.stdin.read()))"
            );
            pb.directory(new File("plugins/intelligence/python"));
            pb.redirectErrorStream(true);

            Process process = pb.start();

            try (OutputStream os = process.getOutputStream()) {
                os.write(requestJson.getBytes(StandardCharsets.UTF_8));
                os.flush();
            }

            String result;
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                result = reader.lines().reduce((a, b) -> a + "\n" + b).orElse("");
            }

            boolean finished = process.waitFor(timeoutMs, TimeUnit.MILLISECONDS);
            if (!finished) {
                process.destroyForcibly();
                log.warn("Intelligence plugin timed out after {}ms", timeoutMs);
                return buildFallbackResult("分析超时");
            }

            if (process.exitValue() != 0) {
                log.warn("Intelligence plugin exited with code {}", process.exitValue());
            }

            return result;

        } catch (Exception e) {
            log.error("Failed to call intelligence plugin", e);
            return buildFallbackResult("插件调用失败: " + e.getMessage());
        }
    }

    private String buildFallbackResult(String message) {
        try {
            Map<String, Object> fallback = Map.of(
                    "pluginVersion", "0.1.0",
                    "code", "PLUGIN_INTERNAL_500",
                    "message", message,
                    "spam", Map.of("label", "unknown", "score", 0.0),
                    "priority", Map.of("label", "normal", "score", 0.0, "reasons", java.util.List.of()),
                    "risk", Map.of("level", "none", "score", 0.0, "indicators", java.util.List.of()),
                    "actions", java.util.List.of()
            );
            return objectMapper.writeValueAsString(fallback);
        } catch (Exception e) {
            return "{}";
        }
    }
}
