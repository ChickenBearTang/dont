package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;


public record GetPostResponseDto(
        Long postId,
        String category,
        Integer generationNo,
        String status,
        String title,
        String content,
        Long authorId,
        String authorNickname,
        String authorProfileImageUrl,
        Boolean isMine,
        Integer likeCount,
        Integer dislikeCount,
        Integer commentCount,
        List<PostAttachmentResponseDto> attachments,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
