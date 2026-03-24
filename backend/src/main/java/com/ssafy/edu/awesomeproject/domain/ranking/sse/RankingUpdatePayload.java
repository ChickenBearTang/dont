package com.ssafy.edu.awesomeproject.domain.ranking.sse;

import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingListResponse;

public record RankingUpdatePayload(Long triggeredUserId, RankingListResponse updatedData) {}
