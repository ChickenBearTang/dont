package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PasswordResetRequestRequestDto(@Email @NotBlank @Size(max = 255) String email) {}
