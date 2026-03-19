package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

// title 필수로 수정
public record UpdatePostRequestDto(@NotBlank @Size(max = 200) String title, String content) {}
