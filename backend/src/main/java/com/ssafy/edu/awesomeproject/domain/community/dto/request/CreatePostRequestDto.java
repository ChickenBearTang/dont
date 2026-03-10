package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreatePostRequestDto (
    @NotBlank String category,
    @NotBlank @Size(max = 200) String title,
    @NotBlank String content
) {}
