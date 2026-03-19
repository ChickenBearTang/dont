package com.ssafy.edu.awesomeproject.domain.fin.global.client.config;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankClient;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class OpenBankConfig {
    @Bean
    public OpenBankClient openBankClient() {
        RestClient restClient = RestClient.builder().baseUrl("https://finopenapi.ssafy.io").build();

        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();

        return factory.createClient(OpenBankClient.class);
    }
}
