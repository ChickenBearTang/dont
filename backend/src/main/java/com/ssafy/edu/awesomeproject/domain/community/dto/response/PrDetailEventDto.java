package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

public record PrDetailEventDto(
        Long eventId,
        String eventType,
        Long actorUserId,
        String payload,
        LocalDateTime createdAt) {}
