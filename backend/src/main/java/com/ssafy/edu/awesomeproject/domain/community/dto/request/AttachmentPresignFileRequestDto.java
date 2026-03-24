package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record AttachmentPresignFileRequestDto(
        @NotBlank String fileName, @NotBlank String contentType, @NotNull Long contentLength) {}
