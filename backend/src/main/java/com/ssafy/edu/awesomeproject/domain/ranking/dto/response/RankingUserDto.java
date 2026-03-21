package com.ssafy.edu.awesomeproject.domain.ranking.dto.response;

public record RankingUserDto(
        Long userId,
        Long score,
        Long rank
) {
    public static RankingUserDto of(Long userId, Long score, Long rank) {
        return new RankingUserDto(userId, score, rank);
    }
}
