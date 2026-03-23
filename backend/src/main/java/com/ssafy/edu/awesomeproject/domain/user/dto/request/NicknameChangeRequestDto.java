package com.ssafy.edu.awesomeproject.domain.user.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record NicknameChangeRequestDto(@NotBlank @Size(min = 2, max = 20) String nickname) {}
