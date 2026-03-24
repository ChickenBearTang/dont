package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiCardRecommendationDbRequest(
        @JsonProperty("user_id") Long userId, String month) {}
