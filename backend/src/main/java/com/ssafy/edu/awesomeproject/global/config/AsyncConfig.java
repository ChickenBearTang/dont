package com.ssafy.edu.awesomeproject.global.config;

import java.util.concurrent.Executor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

@EnableAsync
@Configuration
public class AsyncConfig {

    @Bean(name = "rankingTaskExecutor")
    public Executor rankingTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();


        executor.setCorePoolSize(10);

        executor.setMaxPoolSize(50);

        executor.setQueueCapacity(100);


        executor.setThreadNamePrefix("RankingAsync-");

        executor.initialize();
        return executor;
    }
}
