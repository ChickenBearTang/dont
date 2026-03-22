package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;

public record ProfileImageCompleteRequestDto(@NotBlank String key) {}
