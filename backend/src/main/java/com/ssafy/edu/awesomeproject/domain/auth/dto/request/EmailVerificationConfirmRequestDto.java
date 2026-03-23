package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record EmailVerificationConfirmRequestDto(
        @Email @NotBlank @Size(max = 255) String email,
        @NotBlank @Pattern(regexp = "\\d{6}") String code) {}
