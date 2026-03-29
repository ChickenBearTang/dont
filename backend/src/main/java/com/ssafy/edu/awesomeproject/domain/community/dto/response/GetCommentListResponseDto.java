package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record GetCommentListResponseDto(
        List<CommentThreadDto> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext) {

    public record CommentThreadDto(
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
            LocalDateTime updatedAt,
            Integer replyCount,
            List<CommentReplyDto> replies) {}

    public record CommentReplyDto(
            Long commentId,
            Long parentCommentId,
            Long replyToCommentId,
            String replyToNickname,
            Integer depth,
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
