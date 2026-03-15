package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import java.time.LocalDateTime;
import java.util.List;

//목록 조회
public record GetPostListResponseDto (
    List<PostSummaryDto> content,
    int page,
    int size,
    long totalElements,
    int totalPages,
    boolean hasNext
) {
    public record PostSummaryDto(
        Long postId,
        String category,
        Integer generationNo,
        String title,
        String authorNickname,
        Integer likeCount,
        Integer commentCount,
        LocalDateTime createdAt
    ) {}
}
