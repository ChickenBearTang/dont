package com.ssafy.edu.awesomeproject.domain.notification.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.notification.sse.NotificationSseEmitters;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
public class NotificationSseController {

    private final NotificationSseEmitters notificationSseEmitters;

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter connectNotificationStream(@CurrentUserId Long userId) {
        SseEmitter emitter = new SseEmitter(60 * 60 * 1000L);
        notificationSseEmitters.add(userId, emitter);

        try {
            notificationSseEmitters.sendConnect(userId);
        } catch (Exception e) {
            log.debug("알림 SSE connect 이벤트 발송 실패 후 종료 - userId={}", userId);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
            return emitter;
        }

        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.scheduleAtFixedRate(
            () -> {
                try {
                    notificationSseEmitters.sendHeartbeat(userId);
                } catch (Exception e) {
                    log.debug("알림 SSE heartbeat 스케줄 실행 중 정리 - userId={}", userId);
                }
            },
            25,
            25,
            TimeUnit.SECONDS);

        emitter.onCompletion(scheduler::shutdown);
        emitter.onTimeout(scheduler::shutdown);
        emitter.onError((e) -> scheduler.shutdown());

        return emitter;
    }
}
