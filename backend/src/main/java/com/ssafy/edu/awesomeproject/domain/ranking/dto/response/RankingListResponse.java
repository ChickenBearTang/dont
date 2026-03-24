package com.ssafy.edu.awesomeproject.domain.ranking.dto.response;

import java.util.List;

public record RankingListResponse(List<RankingUserDto> top10, RankingUserDto myRanking) {
    public static RankingListResponse of(List<RankingUserDto> top10, RankingUserDto myRanking) {
        return new RankingListResponse(top10, myRanking);
    }
}
