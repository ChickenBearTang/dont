package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PrVoteSubmitRequestDto(
        @NotBlank @Size(max = 20) String voteValue, @Size(max = 1000) String opinionText) {}
