package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LoginRequestDto(
        @Email @NotBlank String email, @NotBlank @Size(min = 8, max = 255) String password) {}
