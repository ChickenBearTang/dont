package com.ssafy.edu.awesomeproject.domain.ranking.sse;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Component
@RequiredArgsConstructor
public class SseEmitters {

    // Thread-safe 한 단일 서버 인메모리 커넥션 저장소
    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper;

    // 클라이언트 커넥션 추가
    public SseEmitter add(Long userId, SseEmitter emitter) {
        this.emitters.put(userId, emitter);

        log.info("새로운 SSE 연결 추가! User={}, 현재 총 접속자 수 = {}", userId, this.emitters.size());

        // 브라우저 닫힘, 시간 초과, 네트워크 에러 발생 시 메모리 누수를 막기 위한 콜백
        emitter.onCompletion(
                () -> {
                    log.info("SSE 완료 처리됨 (User: {})", userId);
                    this.emitters.remove(userId);
                });
        emitter.onTimeout(
                () -> {
                    log.info("SSE 타임아웃 발생 (User: {})", userId);
                    emitter.complete();
                });
        emitter.onError(
                (e) -> {
                    log.error("SSE 에러 발생 (User: {})", userId, e);
                    emitter.complete();
                });

        return emitter;
    }

    // 단일 서버 메모리 기반 전역(Global) 이벤트 푸시
    public void sendRankingUpdateNotification(RankingUpdatePayload payload) {
        try {
            // 🔥 시니어 최적화: 1만 번 도는 루프 바깥에서 딱 1번만 JSON 변환 수행!
            String jsonPayload = objectMapper.writeValueAsString(payload);

            // 단일 서버의 메모리에 맺혀있는 모든 Emitter들을 순회하며 푸시 이벤트 발송
            emitters.forEach(
                    (userId, emitter) -> {
                        try {
                            emitter.send(
                                    SseEmitter.event().name("ranking-update").data(jsonPayload));
                        } catch (IOException e) {
                            // 클라이언트와의 연결이 물리적으로 끊어진 경우 소켓을 제거
                            log.info("SSE 발송 중 IO 예외 발생 (Client 연결 끊김) - 제거: User {}", userId);
                            emitter.complete();
                            emitters.remove(userId);
                        }
                    });
        } catch (Exception e) {
            log.error("SSE Payload JSON 변환 실패", e);
        }
    }
}
