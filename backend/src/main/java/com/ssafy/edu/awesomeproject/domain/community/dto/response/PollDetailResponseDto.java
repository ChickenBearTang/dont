package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

public record PollDetailResponseDto(
        Long postId,
        String title,
        String content,
        Long authorId,
        String authorNickname,
        String authorProfileImageUrl,
        String question,
        String optionA,
        String optionB,
        LocalDateTime deadlineAt,
        Boolean isClosed,
        Long optionACount,
        Long optionBCount,
        Long totalVoteCount,
        List<PostAttachmentResponseDto> attachments,
        LocalDateTime createdAt,
        LocalDateTime updatedAt) {}
