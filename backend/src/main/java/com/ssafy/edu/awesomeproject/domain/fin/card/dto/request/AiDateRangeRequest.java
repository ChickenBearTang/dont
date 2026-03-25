package com.ssafy.edu.awesomeproject.domain.fin.card.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiDateRangeRequest(
        @JsonProperty("user_id") Long userId,
        @JsonProperty("start_date") String startDate,
        @JsonProperty("end_date") String endDate) {}
