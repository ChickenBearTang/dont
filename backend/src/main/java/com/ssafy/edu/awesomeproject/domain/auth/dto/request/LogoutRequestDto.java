package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.NotBlank;

public record LogoutRequestDto(@NotBlank String refreshToken) { }
