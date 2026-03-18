package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record GetCommentListResponseDto(
        List<CommentSummaryDto> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext) {

    public record CommentSummaryDto(
            Long commentId,
            Long parentCommentId,
            String content,
            Long authorId,
            String authorNickname,
            Boolean isMine,
            Integer likeCount,
            LocalDateTime createdAt) {}
}
