package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.NotBlank;

public record CreateCommentRequestDto(
        // 어떤 댓글에 대댓글 달지
        Long parentCommentId, @NotBlank(message = "content는 필수입니다.") String content) {}
