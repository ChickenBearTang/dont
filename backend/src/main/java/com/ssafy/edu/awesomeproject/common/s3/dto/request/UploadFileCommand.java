package com.ssafy.edu.awesomeproject.common.s3.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record UploadFileCommand(
        @NotBlank String fileName, @NotBlank String contentType, @NotNull Long contentLength) {}
