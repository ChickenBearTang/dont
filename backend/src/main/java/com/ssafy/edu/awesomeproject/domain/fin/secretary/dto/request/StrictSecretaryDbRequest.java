package com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

public record StrictSecretaryDbRequest(
        @JsonProperty("user_id") Long userId,
        @JsonProperty("item_text") String itemText,
        @JsonProperty("item_link") String itemLink,
        @JsonProperty("user_reason") String userReason) {}
