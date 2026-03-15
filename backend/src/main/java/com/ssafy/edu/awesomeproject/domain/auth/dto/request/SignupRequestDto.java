package com.ssafy.edu.awesomeproject.domain.auth.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SignupRequestDto(
    @Email @NotBlank String email,
    @NotBlank @Size(min = 8, max = 255) String password,
    @NotNull Integer generationNo) {

}
