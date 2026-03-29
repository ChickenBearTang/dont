package com.ssafy.edu.awesomeproject.domain.dummy.client.config;

import com.ssafy.edu.awesomeproject.domain.dummy.client.DummyCardClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class DummyCardClientConfig {
    @Bean
    public DummyCardClient dummyCardClient() {
        RestClient restClient = RestClient.builder().baseUrl("https://finopenapi.ssafy.io").build();
        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();
        return factory.createClient(DummyCardClient.class);
    }
}
