package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
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
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record PostSummaryDto(
        Long postId,
        String category,
        Integer generationNo,
        String title,
        String authorNickname,
        Integer likeCount,
        Integer commentCount,
        LocalDateTime createdAt,
        PostExtraSummaryDto extraSummary
    ) {}

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record PostExtraSummaryDto(
        PrSummaryDto pr
        HotdealSummaryDto hotdeal
    ) {}

    public record HotdealSummaryDto(
        Long dealPriceAmount,
        Long originalPriceAmount,
        String storeName,
        LocalDateTime expiredAt,
        Boolean isExpired
    ) {}

    public record PrSummaryDto(
        String status,
        String resultStatus,
        Long totalVoteCount,
        LocalDateTime deadlineAt
    ) {}
}
