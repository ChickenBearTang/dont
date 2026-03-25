package com.ssafy.edu.awesomeproject.domain.ranking.dto.response;

public record RankingUserDto(
        Long userId,
        String nickname,
        Long score,
        Long rank,
        Integer cohortNo,
        String profileImageUrl) {
    public static RankingUserDto of(
            Long userId,
            String nickname,
            Long score,
            Long rank,
            Integer cohortNo,
            String profileImageUrl) {
        return new RankingUserDto(userId, nickname, score, rank, cohortNo, profileImageUrl);
    }
}
