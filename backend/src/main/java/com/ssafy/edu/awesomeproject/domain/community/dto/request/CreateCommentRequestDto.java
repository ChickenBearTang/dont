package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;

public record CreateCommentRequestDto(
        Long parentCommentId, @NotBlank(message = "content는 필수입니다.") String content) {}
