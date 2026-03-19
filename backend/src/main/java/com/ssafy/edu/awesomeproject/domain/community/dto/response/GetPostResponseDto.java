package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;

// 게시글 상세조회 -> get/posts/postId
public record GetPostResponseDto(
        Long postId,
        String category,
        Integer generationNo,
        String title,
        String content,
        Long authorId,
        String authorNickname,
        Boolean isMine,
        Integer likeCount,
        Integer dislikeCount,
        Integer commentCount,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
