package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.NotBlank;

public record TokenReissueRequestDto (@NotBlank String refreshToken){ }
