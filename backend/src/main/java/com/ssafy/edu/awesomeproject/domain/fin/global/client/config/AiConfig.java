package com.ssafy.edu.awesomeproject.domain.fin.global.client.config;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class AiConfig {

    @Value("${ai.server.url:http://127.0.0.1:18000}")
    private String aiServerUrl;

    @Value("${ai.server.connect-timeout-ms:2000}")
    private int connectTimeoutMs;

    @Value("${ai.server.read-timeout-ms:20000}")
    private int readTimeoutMs;

    @Bean
    public AiClient aiClient() {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(connectTimeoutMs);
        requestFactory.setReadTimeout(readTimeoutMs);

        RestClient restClient =
                RestClient.builder().baseUrl(aiServerUrl).requestFactory(requestFactory).build();

        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();

        return factory.createClient(AiClient.class);
    }
}
