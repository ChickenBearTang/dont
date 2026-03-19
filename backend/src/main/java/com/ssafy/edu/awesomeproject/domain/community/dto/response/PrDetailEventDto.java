package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.LocalDateTime;

public record PrDetailEventDto(
        Long eventId,
        String eventType,
        Long actorUserId,
        String actorNickname,
        String actorProfileImageUrl,
        JsonNode payload,
        LocalDateTime createdAt) {}
