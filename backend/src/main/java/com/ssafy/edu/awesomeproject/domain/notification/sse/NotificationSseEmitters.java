package com.ssafy.edu.awesomeproject.domain.notification.sse;

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
public class NotificationSseEmitters {

    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();
    private final ObjectMapper objectMapper;

    public SseEmitter add(Long userId, SseEmitter emitter) {
        SseEmitter oldEmitter = emitters.put(userId, emitter);

        if (oldEmitter != null) {
            try {
                oldEmitter.complete();
            } catch (Exception ignored) {
            }
        }

        log.info("알림 SSE 연결 추가 - userId={}, 현재 연결 수={}", userId, emitters.size());

        emitter.onCompletion(() -> {
            log.info("알림 SSE 완료 - userId={}", userId);
            emitters.remove(userId, emitter);
        });

        emitter.onTimeout(() -> {
            log.info("알림 SSE 타임아웃 - userId={}", userId);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        });

        emitter.onError((e) -> {
            log.debug("알림 SSE 연결 종료(onError) - userId={}", userId);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        });

        return emitter;
    }

    public void sendConnect(Long userId) {
        sendEvent(userId, "connect", "Connected successfully to Notification Stream.");
    }

    public void sendHeartbeat(Long userId) {
        sendEvent(userId, "heartbeat", "ping");
    }

    public void sendReadAll(Long userId) {
        sendEvent(userId, "notification-read-all", "all-read");
    }

    public void sendRead(Long userId, Long notificationId) {
        sendEvent(userId, "notification-read", String.valueOf(notificationId));
    }

    public void sendToUser(Long userId, NotificationSsePayload payload) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter == null) {
            return;
        }

        try {
            String jsonPayload = objectMapper.writeValueAsString(payload);
            emitter.send(SseEmitter.event().name("notification-created").data(jsonPayload));
        } catch (IOException | IllegalStateException e) {
            log.debug("알림 SSE 발송 중 종료된 연결 정리 - userId={}", userId);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        } catch (Exception e) {
            log.warn("알림 SSE payload 직렬화/발송 실패 - userId={}", userId, e);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        }
    }

    private void sendEvent(Long userId, String eventName, String data) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter == null) {
            return;
        }

        try {
            emitter.send(SseEmitter.event().name(eventName).data(data));
        } catch (IOException | IllegalStateException e) {
            log.debug("알림 SSE {} 발송 중 종료된 연결 정리 - userId={}", eventName, userId);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        } catch (Exception e) {
            log.warn("알림 SSE {} 발송 실패 - userId={}", eventName, userId, e);
            emitters.remove(userId, emitter);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        }
    }
}
