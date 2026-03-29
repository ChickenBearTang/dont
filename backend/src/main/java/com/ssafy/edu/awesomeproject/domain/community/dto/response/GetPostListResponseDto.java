package com.ssafy.edu.awesomeproject.domain.community.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.time.LocalDateTime;
import java.util.List;


public record GetPostListResponseDto(
        List<PostSummaryDto> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean hasNext) {

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record PostSummaryDto(
            Long postId,
            String category,
            Integer generationNo,
            String status,
            String title,
            Long authorId,
            String authorNickname,
            String authorProfileImageUrl,
            Boolean isMine,
            Integer likeCount,
            Integer commentCount,
            Integer attachmentCount,
            LocalDateTime createdAt,
            PostExtraSummaryDto extraSummary) {}

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record PostExtraSummaryDto(
            PrSummaryDto pr, HotdealSummaryDto hotdeal, PollSummaryDto poll) {}

    public record HotdealSummaryDto(
            Long dealPriceAmount,
            Long originalPriceAmount,
            String storeName,
            LocalDateTime expiredAt,
            Boolean isExpired) {}

    public record PrSummaryDto(
            String status,
            String resultStatus,
            String itemName,
            Long priceAmount,
            Long totalVoteCount,
            LocalDateTime deadlineAt) {}

    public record PollSummaryDto(
            String question,
            String optionA,
            String optionB,
            LocalDateTime deadlineAt,
            Boolean isClosed,
            Long optionACount,
            Long optionBCount,
            Long totalVoteCount) {}
}
