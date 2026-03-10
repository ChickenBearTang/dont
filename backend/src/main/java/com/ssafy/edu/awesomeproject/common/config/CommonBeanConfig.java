package com.ssafy.edu.awesomeproject.common.config;

import java.time.Clock;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class CommonBeanConfig {

    @Bean
    public Clock applicationClock() {
        return Clock.systemUTC();
    }
}
