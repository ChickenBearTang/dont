package com.ssafy.edu.awesomeproject.domain.fin.global.client.config;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class AiConfig {

    @Value("${ai.server.url:http://localhost:8000}")
    private String aiServerUrl;

    @Bean
    public AiClient aiClient() {
        RestClient restClient = RestClient.builder().baseUrl(aiServerUrl).build();

        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();

        return factory.createClient(AiClient.class);
    }
}
