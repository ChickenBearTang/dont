package com.ssafy.edu.awesomeproject.domain.ranking.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.ranking.sse.SseEmitters;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/ranking")
@RequiredArgsConstructor
public class RankingSseController {

    private final SseEmitters sseEmitters;


    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter connectRankingStream(@CurrentUserId Long userId) {


        SseEmitter emitter = new SseEmitter(60 * 60 * 1000L);


        sseEmitters.add(userId, emitter);

        try {


            emitter.send(
                    SseEmitter.event()
                            .name("connect")
                            .data("Connected successfully to Single Server MVP Ranking Stream."));
        } catch (Exception e) {
            log.error("SSE 초기 연결 이벤트 발송 실패 - User: {}", userId, e);
            emitter.completeWithError(e);
        }

        return emitter;
    }
}
