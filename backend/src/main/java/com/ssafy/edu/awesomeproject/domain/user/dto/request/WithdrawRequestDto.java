package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record WithdrawRequestDto(@NotBlank @Size(min = 8, max = 255) String currentPassword) {}
