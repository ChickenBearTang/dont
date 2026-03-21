package com.ssafy.edu.awesomeproject.domain.ranking.service;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RankingService {

    private final StringRedisTemplate redisTemplate;

    // 글로벌 전체 랭킹용 Redis Key
    private static final String TOTAL_RANKING_KEY = "ranking:savebox:total";
    // 기수별 랭킹용 Redis Key Prefix
    private static final String COHORT_RANKING_PREFIX = "ranking:savebox:cohort:";
    // 동점자 방지 처리(Tie-Breaker)를 위한 미래 기준점 (약 2099년)
    private static final double MAX_TIME_MS = 4102444800000.0;

    /**
     * 잔액 변경 시 ZSET에 랭킹 스코어를 업데이트합니다. (동점자 정밀 처리 포함)
     *
     * @param userId  유저 ID
     * @param balance 최신 잔액
     * @param cohort  유저의 소속 기수
     */
    public void updateSaveboxRanking(Long userId, Long balance, Integer cohort) {
        long currentTimeMs = System.currentTimeMillis();
        
        // 동점자 발생 시, 먼저 저축한(시간이 더 과거인) 유저가 더 큰 소수점을 취득하게 되어 상위 랭크를 보장
        double tieBreaker = 1.0 - (currentTimeMs / MAX_TIME_MS);
        double score = balance + tieBreaker;

        // 1. 전체 랭킹 업데이트
        redisTemplate.opsForZSet().add(TOTAL_RANKING_KEY, String.valueOf(userId), score);

        // 2. 소속 기수(Cohort)별 랭킹 업데이트
        if (cohort != null && cohort > 0) {
            String cohortKey = COHORT_RANKING_PREFIX + cohort;
            redisTemplate.opsForZSet().add(cohortKey, String.valueOf(userId), score);
        }
    }
}
