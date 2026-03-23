package com.ssafy.edu.awesomeproject.domain.ranking.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingUserDto;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations.TypedTuple;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RankingService {

    private final StringRedisTemplate redisTemplate;
    private final UserRepository userRepository;

    // 글로벌 전체 랭킹용 Redis Key
    private static final String TOTAL_RANKING_KEY = "ranking:savebox:total";
    // 기수별 랭킹용 Redis Key Prefix
    private static final String COHORT_RANKING_PREFIX = "ranking:savebox:cohort:";
    // 동점자 방지 처리(Tie-Breaker)를 위한 미래 기준점 (약 2099년)
    private static final double MAX_TIME_MS = 4102444800000.0;

    /**
     * 잔액 변경 시 ZSET에 랭킹 스코어를 업데이트합니다. (동점자 정밀 처리 포함)
     *
     * @param userId 유저 ID
     * @param balance 최신 잔액
     * @param cohort 유저의 소속 기수
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

    /** Top 10 랭킹 리스트 조회 (cohort 인자가 null이면 전체 랭킹 조회) */
    public List<RankingUserDto> getTop10Ranking(Integer cohort) {
        String key =
                (cohort != null && cohort > 0) ? COHORT_RANKING_PREFIX + cohort : TOTAL_RANKING_KEY;
        Set<TypedTuple<String>> top10 =
                redisTemplate.opsForZSet().reverseRangeWithScores(key, 0, 9);

        if (top10 == null || top10.isEmpty()) return List.of();

        long currentRank = 1;
        List<RankingUserDto> result = new ArrayList<>();
        List<Long> userIds = new ArrayList<>();
        List<Double> scores = new ArrayList<>();

        for (TypedTuple<String> tuple : top10) {
            Long id = Long.valueOf(tuple.getValue());
            Double score = tuple.getScore();
            if (score != null) {
                userIds.add(id);
                scores.add(score);
            }
        }

        Map<Long, String> nicknameMap = userRepository.findAllById(userIds).stream()
                .collect(Collectors.toMap(User::getId, User::getNickname));

        for (int i = 0; i < userIds.size(); i++) {
            Long userId = userIds.get(i);
            String nickname = nicknameMap.getOrDefault(userId, "탈퇴한 유저");
            result.add(RankingUserDto.of(userId, nickname, scores.get(i).longValue(), currentRank++));
        }

        return result;
    }

    /** 내 랭킹 조회 (존재하지 않으면 rank = -1 로 반환) */
    public RankingUserDto getMyRanking(Long userId, Integer cohort) {
        String key =
                (cohort != null && cohort > 0) ? COHORT_RANKING_PREFIX + cohort : TOTAL_RANKING_KEY;
        String userIdStr = String.valueOf(userId);

        Double scoreDouble = redisTemplate.opsForZSet().score(key, userIdStr);
        Long rank = redisTemplate.opsForZSet().reverseRank(key, userIdStr);

        if (scoreDouble == null || rank == null) {
            return RankingUserDto.of(userId, null, 0L, -1L);
        }

        String nickname = userRepository.findById(userId)
                .map(User::getNickname)
                .orElse("탈퇴한 유저");

        return RankingUserDto.of(
                userId, nickname, scoreDouble.longValue(), rank + 1); // Redis ZSET Rank는 0부터 시작하므로 +1
    }
}
