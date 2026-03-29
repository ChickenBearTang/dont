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
        if (oldEmitter != null && oldEmitter != emitter) {
            safeComplete(oldEmitter);
        }

        emitter.onCompletion(() -> emitters.remove(userId, emitter));

        emitter.onTimeout(() -> {
            log.info("Notification SSE timeout - userId={}", userId);
            emitters.remove(userId, emitter);
        });

        emitter.onError((e) -> {
            log.debug("Notification SSE connection closed by error - userId={}", userId);
            emitters.remove(userId, emitter);
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
            log.debug("Notification SSE send skipped. Emitter is already closed - userId={}", userId);
            emitters.remove(userId, emitter);
        } catch (Exception e) {
            log.warn("Notification SSE payload send failed - userId={}", userId, e);
            emitters.remove(userId, emitter);
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
            log.debug("Notification SSE {} send skipped. Emitter is already closed - userId={}", eventName, userId);
            emitters.remove(userId, emitter);
        } catch (Exception e) {
            log.warn("Notification SSE {} send failed - userId={}", eventName, userId, e);
            emitters.remove(userId, emitter);
        }
    }

    private void safeComplete(SseEmitter emitter) {
        try {
            emitter.complete();
        } catch (Exception ignored) {
        }
    }
}
