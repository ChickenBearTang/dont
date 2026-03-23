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
        
        // 단일 EC2 서버의 자원 한계를 고려한 OOM 방지용 스레드 풀 최적화 설정
        // 1. CorePoolSize: 평소 유지할 기본 워커 스레드 개수
        executor.setCorePoolSize(10);     
        // 2. MaxPoolSize: 트래픽 스파이크 시 최대로 생성할 스레드 개수 (무한 생성을 막아 서버 메모리 폭발 방어)
        executor.setMaxPoolSize(50);      
        // 3. QueueCapacity: MaxPoolSize 초과 시 대기시킬 작업 큐의 최대 용량
        executor.setQueueCapacity(100);   
        
        // 4. 스레드 로깅 및 모니터링 식별을 위한 접두사 추가
        executor.setThreadNamePrefix("RankingAsync-");
        
        executor.initialize();
        return executor;
    }
}
