package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

// 게시글 상세조회 -> get/posts/postId
public record GetPostResponseDto (
    Long postId,
    String category,
    Long cohortId,
    String title,
    String content,
    String authorNickname,
    Integer likeCount,
    Integer dislikeCount,
    Integer commentCount,
    LocalDateTime createdAt,
    LocalDateTime updatedAt
) {}
