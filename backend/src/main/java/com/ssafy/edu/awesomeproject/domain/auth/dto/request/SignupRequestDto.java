package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record SignupRequestDto(
        @Email @NotBlank @Size(max = 255) String email,
        @NotBlank @Size(min = 8, max = 255) String password,
        @NotBlank @Size(max = 50) String name,
        @NotNull @Past LocalDate birthDate,
        @NotBlank @Size(max = 60) String nickname,
        @NotNull @AssertTrue Boolean termsAgreed,
        @NotNull @Positive Long cohortId) {}
