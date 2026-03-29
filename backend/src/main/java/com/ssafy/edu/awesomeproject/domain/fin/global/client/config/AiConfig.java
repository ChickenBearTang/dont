package com.ssafy.edu.awesomeproject.domain.fin.global.client.config;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
@Slf4j
public class AiConfig {

    private static final String FIXED_PORT = "18000";
    private static final String FALLBACK_BASE_URL = "http://127.0.0.1:18000";

    @Value("${ai.server.url:http://127.0.0.1:18000}")
    private String aiServerUrl;

    @Value("${ai.server.connect-timeout-ms:2000}")
    private int connectTimeoutMs;

    @Value("${ai.server.read-timeout-ms:60000}")
    private int readTimeoutMs;

    @Bean
    public AiClient aiClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(connectTimeoutMs);
        requestFactory.setReadTimeout(readTimeoutMs);

        String resolvedAiServerUrl = resolveAiServerUrl(aiServerUrl);
        RestClient restClient =
                RestClient.builder()
                        .baseUrl(resolvedAiServerUrl)
                        .requestFactory(requestFactory)
                        .build();

        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();

        return factory.createClient(AiClient.class);
    }

    private String resolveAiServerUrl(String configuredUrl) {
        if (configuredUrl == null || configuredUrl.isBlank()) {
            return FALLBACK_BASE_URL;
        }
        String trimmed = configuredUrl.trim();
        if (!trimmed.contains(":8000")) {
            return trimmed;
        }
        String corrected = trimmed.replace(":8000", ":" + FIXED_PORT);
        log.warn(
                "Detected deprecated AI endpoint port in ai.server.url ({}). Using {} instead.",
                trimmed,
                corrected);
        return corrected;
    }
}
