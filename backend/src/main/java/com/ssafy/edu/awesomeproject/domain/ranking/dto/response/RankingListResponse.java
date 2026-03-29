package com.ssafy.edu.awesomeproject.domain.ranking.dto.response;

import java.util.List;

public record RankingListResponse(List<RankingUserDto> top100, RankingUserDto myRanking) {
    public static RankingListResponse of(List<RankingUserDto> top100, RankingUserDto myRanking) {
        return new RankingListResponse(top100, myRanking);
    }
}
