package com.ssafy.edu.awesomeproject.domain.ranking.controller;

import com.ssafy.edu.awesomeproject.domain.ranking.sse.SseEmitters;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/api/ranking")
@RequiredArgsConstructor
public class RankingSseController {

    private final SseEmitters sseEmitters;

    /**
     * 클라이언트(프론트엔드)가 랭킹 실시간 업데이트를 구독하기 위한 단방향 SSE 스트림 엔드포인트
     */
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter connectRankingStream(@RequestAttribute("userId") Long userId) {
        
        // 커넥션 지속 시간을 최대 60분(3600초)으로 설정 (로드밸런서 및 프록시의 Timeout 설정과 동기화 필요)
        SseEmitter emitter = new SseEmitter(60 * 60 * 1000L);
        
        // 인메모리 커넥션 풀에 담아 생명주기 제어 시작
        sseEmitters.add(userId, emitter);

        try {
            // [중요 시니어 디테일]
            // Nginx나 AWS ALB 등 앞단의 프록시에서 초기 데이터가 없어 502/504 에러를 내뿜지 않도록, 
            // 연결되자마자 즉시 빈 "connect" 이벤트를 강제로 쏴서 파이프가 열려있음을 보장합니다.
            emitter.send(SseEmitter.event()
                    .name("connect")
                    .data("Connected successfully to Single Server MVP Ranking Stream."));
        } catch (Exception e) {
            log.error("SSE 초기 연결 이벤트 발송 실패 - User: {}", userId, e);
            emitter.completeWithError(e);
        }

        return emitter;
    }
}
