package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record SignupRequestDto(
        @NotBlank
                @Size(max = 255)
                @Pattern(
                        regexp = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                        message = "올바른 이메일 형식을 입력해주세요.")
                String email,
        @NotBlank
                @Size(min = 8, max = 72)
                @Pattern(
                        regexp =
                                "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{8,72}$",
                        message = "비밀번호는 영문 대/소문자, 숫자, 특수문자를 포함해 8자 이상 72자 이하여야 합니다.")
                String password,
        @NotBlank @Size(max = 50) String name,
        @NotNull @Past LocalDate birthDate,
        @NotBlank @Size(max = 60) String nickname,
        @NotNull @AssertTrue Boolean termsAgreed,
        @NotNull @Positive Long cohortId) {}
