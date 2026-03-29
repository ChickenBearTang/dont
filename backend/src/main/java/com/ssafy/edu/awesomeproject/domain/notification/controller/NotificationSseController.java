package com.ssafy.edu.awesomeproject.domain.notification.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.notification.sse.NotificationSseEmitters;
import jakarta.annotation.PreDestroy;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/notifications")
public class NotificationSseController {

    private final NotificationSseEmitters notificationSseEmitters;
    private final ScheduledExecutorService heartbeatScheduler;
    private final ConcurrentHashMap<Long, ScheduledFuture<?>> heartbeatTasks = new ConcurrentHashMap<>();
    private final int heartbeatSeconds;
    private final long emitterTimeoutMillis;

    public NotificationSseController(
        NotificationSseEmitters notificationSseEmitters,
        @Value("${notification.sse.scheduler-pool-size}") int schedulerPoolSize,
        @Value("${notification.sse.heartbeat-seconds}") int heartbeatSeconds,
        @Value("${notification.sse.emitter-timeout-millis}") long emitterTimeoutMillis) {
        this.notificationSseEmitters = notificationSseEmitters;
        this.heartbeatScheduler = Executors.newScheduledThreadPool(schedulerPoolSize);
        this.heartbeatSeconds = heartbeatSeconds;
        this.emitterTimeoutMillis = emitterTimeoutMillis;
    }

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter connectNotificationStream(@CurrentUserId Long userId) {
        SseEmitter emitter = new SseEmitter(emitterTimeoutMillis);
        notificationSseEmitters.add(userId, emitter);

        try {
            notificationSseEmitters.sendConnect(userId);
        } catch (Exception e) {
            log.debug("Notification SSE connect event send failed - userId={}", userId);
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
            return emitter;
        }

        ScheduledFuture<?> heartbeatTask = heartbeatScheduler.scheduleAtFixedRate(
            () -> {
                try {
                    notificationSseEmitters.sendHeartbeat(userId);
                } catch (Exception e) {
                    log.debug("SSE heartbeat failed or emitter already closed - userId={}", userId);
                }
            },
            heartbeatSeconds,
            heartbeatSeconds,
            TimeUnit.SECONDS);

        ScheduledFuture<?> previousTask = heartbeatTasks.put(userId, heartbeatTask);
        if (previousTask != null) {
            previousTask.cancel(true);
        }

        emitter.onCompletion(() -> cancelHeartbeatTask(userId, heartbeatTask));
        emitter.onTimeout(() -> cancelHeartbeatTask(userId, heartbeatTask));
        emitter.onError((e) -> cancelHeartbeatTask(userId, heartbeatTask));

        return emitter;
    }

    private void cancelHeartbeatTask(Long userId, ScheduledFuture<?> task) {
        heartbeatTasks.compute(
            userId,
            (id, currentTask) -> {
                if (currentTask == task) {
                    currentTask.cancel(true);
                    return null;
                }
                return currentTask;
            });
    }

    @PreDestroy
    public void shutdownHeartbeatScheduler() {
        heartbeatTasks.values().forEach((task) -> task.cancel(true));
        heartbeatTasks.clear();
        heartbeatScheduler.shutdownNow();
    }
}
