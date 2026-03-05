package com.ssafy.edu.awesomeproject.sample.presentation;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record EchoRequest(
        @Schema(description = "에코할 메시지", example = "Hello, World!", maxLength = 200)
                @NotBlank(message = "message must not be blank.")
                @Size(max = 200, message = "message must be less than or equal to 200 characters.")
                String message) {}
