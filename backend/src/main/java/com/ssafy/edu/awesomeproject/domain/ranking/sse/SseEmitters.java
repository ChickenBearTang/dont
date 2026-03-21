package com.ssafy.edu.awesomeproject.domain.ranking.sse;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class SseEmitters {

    // Thread-safe 한 단일 서버 인메모리 커넥션 저장소
    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();

    // 클라이언트 커넥션 추가
    public SseEmitter add(Long userId, SseEmitter emitter) {
        this.emitters.put(userId, emitter);
        
        log.info("새로운 SSE 연결 추가! User={}, 현재 총 접속자 수 = {}", userId, this.emitters.size());
        
        // 브라우저 닫힘, 시간 초과, 네트워크 에러 발생 시 메모리 누수를 막기 위한 콜백
        emitter.onCompletion(() -> {
            log.info("SSE 완료 처리됨 (User: {})", userId);
            this.emitters.remove(userId);
        });
        emitter.onTimeout(() -> {
            log.info("SSE 타임아웃 발생 (User: {})", userId);
            emitter.complete();
        });
        emitter.onError((e) -> {
            log.error("SSE 에러 발생 (User: {})", userId, e);
            emitter.complete();
        });

        return emitter;
    }

    // 단일 서버 메모리 기반 전역(Global) 이벤트 푸시
    public void sendRankingUpdateNotification(Long triggeredUserId) {
        // 단일 서버의 메모리에 맺혀있는 모든 Emitter들을 순회하며 푸시 이벤트 발송
        emitters.forEach((userId, emitter) -> {
            try {
                // 프론트엔드의 RankingUpdatePayload 인터페이스 형태에 맞춘 JSON 직렬화 문자열 발송
                String jsonPayload = String.format("{\"triggeredUserId\": %d}", triggeredUserId);

                // "ranking-update" 라는 커스텀 이벤트 채널을 통해 트리거 발동
                emitter.send(SseEmitter.event()
                        .name("ranking-update")
                        .data(jsonPayload)); // 프론트엔드 JSON.parse() 에러(Unexpected token U) 해결
            } catch (IOException e) {
                // 클라이언트와의 연결이 물리적으로 끊어진 경우 소켓을 제거
                log.info("SSE 발송 중 IO 예외 발생 (Client 연결 끊김) - 제거: User {}", userId);
                emitter.complete();
                emitters.remove(userId);
            }
        });
    }
}
