package com.example.emailsystem.intelligence.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(IntelligenceLlmProperties.class)
public class IntelligenceRestClientConfig {

    @Bean
    public RestClient intelligenceRestClient(RestClient.Builder builder,
                                             IntelligenceLlmProperties props) {
        return builder
            .baseUrl(props.baseUrl())
            .defaultHeader("Authorization", "Bearer " + props.apiKey())
            .defaultHeader("Content-Type", "application/json")
            .build();
    }
}
