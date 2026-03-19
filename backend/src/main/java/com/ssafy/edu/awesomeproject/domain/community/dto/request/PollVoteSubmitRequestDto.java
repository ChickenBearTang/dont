package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PollVoteSubmitRequestDto(@NotBlank @Size(max = 20) String voteOption) {}
