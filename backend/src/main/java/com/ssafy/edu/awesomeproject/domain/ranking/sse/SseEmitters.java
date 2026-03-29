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

    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper;

    public SseEmitter add(Long userId, SseEmitter emitter) {
        SseEmitter oldEmitter = emitters.put(userId, emitter);
        if (oldEmitter != null && oldEmitter != emitter) {
            safeComplete(oldEmitter);
        }

        log.info("Ranking SSE connected - userId={}, totalConnections={}", userId, emitters.size());

        emitter.onCompletion(() -> {
            log.info("Ranking SSE completed - userId={}", userId);
            emitters.remove(userId, emitter);
        });

        emitter.onTimeout(() -> {
            log.info("Ranking SSE timeout - userId={}", userId);
            emitters.remove(userId, emitter);
        });

        emitter.onError((e) -> {
            log.debug("Ranking SSE closed by error - userId={}", userId, e);
            emitters.remove(userId, emitter);
        });

        return emitter;
    }

    public void sendRankingUpdateNotification(RankingUpdatePayload payload) {
        try {
            String jsonPayload = objectMapper.writeValueAsString(payload);

            emitters.forEach((userId, emitter) -> {
                try {
                    emitter.send(SseEmitter.event().name("ranking-update").data(jsonPayload));
                } catch (IOException | IllegalStateException e) {
                    log.debug("Ranking SSE emitter closed while sending - userId={}", userId);
                    emitters.remove(userId, emitter);
                } catch (Exception e) {
                    log.warn("Ranking SSE send failed - userId={}", userId, e);
                    emitters.remove(userId, emitter);
                }
            });
        } catch (Exception e) {
            log.error("Ranking SSE payload serialization failed", e);
        }
    }

    private void safeComplete(SseEmitter emitter) {
        try {
            emitter.complete();
        } catch (Exception ignored) {
        }
    }
}
