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
        String status,
        String content,
        Long authorId,
        String authorNickname,
        String authorProfileImageUrl,
        Boolean isMine,
        Integer likeCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
}
