package com.ssafy.edu.awesomeproject.domain.dummy.client.config;

import com.ssafy.edu.awesomeproject.domain.dummy.client.FinanceMemberClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class FinanceMemberClientConfig {
    @Bean
    public FinanceMemberClient financeMemberClient() {
        RestClient restClient = RestClient.builder().baseUrl("https://finopenapi.ssafy.io").build();
        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();
        return factory.createClient(FinanceMemberClient.class);
    }
}
