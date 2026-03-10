package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Size;

public record UpdatePostRequestDto (
    @Size(max = 200) String title,
    String content
) {}
