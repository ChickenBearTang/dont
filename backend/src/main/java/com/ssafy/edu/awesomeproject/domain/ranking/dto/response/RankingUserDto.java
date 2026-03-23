package com.ssafy.edu.awesomeproject.domain.ranking.dto.response;

public record RankingUserDto(
        Long userId,
        String nickname,
        Long score,
        Long rank
) {
    public static RankingUserDto of(Long userId, String nickname, Long score, Long rank) {
        return new RankingUserDto(userId, nickname, score, rank);
    }
}
