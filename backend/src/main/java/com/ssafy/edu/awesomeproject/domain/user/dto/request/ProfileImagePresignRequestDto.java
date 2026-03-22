package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record ProfileImagePresignRequestDto(
        @NotBlank String fileName,
        @NotBlank String contentType,
        @NotNull @Positive Long contentLength) {}
