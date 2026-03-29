package com.ssafy.edu.awesomeproject.domain.ranking.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingUserDto;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations.TypedTuple;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class RankingService {

    private final StringRedisTemplate redisTemplate;
    private final UserRepository userRepository;
    private final S3AssetUrlResolver s3AssetUrlResolver;

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

    /** 매일 자정(00:00:01)에 현재 랭킹 상태를 스냅샷으로 저장합니다. 이 스냅샷은 '오늘 하루 동안의 순위 변동(▲/▼)'을 계산하는 기준점이 됩니다. */
    @Scheduled(cron = "1 0 0 * * *")
    public void createDailyRankingSnapshot() {
        log.info("[Ranking Snapshot] Starting daily ranking snapshot creation...");
        saveSnapshot(TOTAL_RANKING_KEY, "ranking:snapshot:total");

        // 기수별 스냅샷도 생성 (필요 시)
        // 실제로는 기수가 많을 수 있으므로 활성 기수만 하거나,
        // 조회 시점에 스냅샷이 없으면 그때 생성하는 Lazy 방식과 병행하는 것이 좋습니다.
    }

    private void saveSnapshot(String sourceKey, String snapshotKey) {
        Set<String> range = redisTemplate.opsForZSet().reverseRange(sourceKey, 0, -1);
        if (range == null || range.isEmpty()) return;

        redisTemplate.delete(snapshotKey);
        int rank = 1;
        for (String userId : range) {
            redisTemplate.opsForHash().put(snapshotKey, userId, String.valueOf(rank++));
        }
        log.info("[Ranking Snapshot] Saved snapshot to {} (count: {})", snapshotKey, range.size());
    }

    /** Top 10 랭킹 리스트 조회 (cohort 인자가 null이면 전체 랭킹 조회) */
    public List<RankingUserDto> getTop10Ranking(Integer cohort) {
        String key =
                (cohort != null && cohort > 0) ? COHORT_RANKING_PREFIX + cohort : TOTAL_RANKING_KEY;
        String snapshotKey =
                (cohort != null && cohort > 0)
                        ? "ranking:snapshot:cohort:" + cohort
                        : "ranking:snapshot:total";

        // 🔥 로컬 테스트/초기 구동 지원: 스냅샷이 없으면 현재 상태로 즉시 생성 (최초 1회)
        if (Boolean.FALSE.equals(redisTemplate.hasKey(snapshotKey))) {
            log.info(
                    "[Ranking Snapshot] Snapshot not found for {}. Creating initial snapshot...",
                    snapshotKey);
            saveSnapshot(key, snapshotKey);
        }

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

        // 유저 정보를 한 번에 조회 (N+1 방지)
        Map<Long, User> userMap =
                userRepository.findAllById(userIds).stream()
                        .collect(Collectors.toMap(User::getId, u -> u));

        // 어제 랭킹 스냅샷 조회 (Redis Hash: userId -> rank)
        Map<Object, Object> snapshotMap = redisTemplate.opsForHash().entries(snapshotKey);

        for (int i = 0; i < userIds.size(); i++) {
            Long userId = userIds.get(i);
            User user = userMap.get(userId);
            String nickname = user != null ? user.getNickname() : "탈퇴한 유저";

            // 등락 계산 (rankDiff = 어제순위 - 현재순위)
            Integer rankDiff = 0;
            if (!snapshotMap.isEmpty() && snapshotMap.containsKey(userId.toString())) {
                try {
                    long lastRank = Long.parseLong(snapshotMap.get(userId.toString()).toString());
                    rankDiff = (int) (lastRank - currentRank);
                } catch (NumberFormatException ignored) {
                }
            }

            Integer cohortNo =
                    (user != null && user.getCohort() != null)
                            ? user.getCohort().getGenerationNo()
                            : null;
            String profileImageUrl =
                    user != null
                            ? s3AssetUrlResolver.resolvePublicUrlOrNull(user.getProfileImageUrl())
                            : null;

            result.add(
                    RankingUserDto.of(
                            userId,
                            nickname,
                            scores.get(i).longValue(),
                            currentRank++,
                            cohortNo,
                            profileImageUrl,
                            rankDiff));
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
            return RankingUserDto.of(userId, null, 0L, -1L, null, null, 0);
        }

        User user = userRepository.findById(userId).orElse(null);
        String nickname = user != null ? user.getNickname() : "탈퇴한 유저";

        // 내 랭킹 등락 계산
        String snapshotKey =
                (cohort != null && cohort > 0)
                        ? "ranking:snapshot:cohort:" + cohort
                        : "ranking:snapshot:total";

        // 🔥 로컬 테스트/초기 구동 지원: 스냅샷이 없으면 현재 상태로 즉시 생성
        if (Boolean.FALSE.equals(redisTemplate.hasKey(snapshotKey))) {
            saveSnapshot(key, snapshotKey);
        }

        Object lastRankObj = redisTemplate.opsForHash().get(snapshotKey, userIdStr);
        Integer rankDiff = 0;
        long currentRank = rank + 1;
        if (lastRankObj != null) {
            try {
                long lastRank = Long.parseLong(lastRankObj.toString());
                rankDiff = (int) (lastRank - currentRank);
            } catch (NumberFormatException ignored) {
            }
        }

        Integer cohortNo =
                (user != null && user.getCohort() != null)
                        ? user.getCohort().getGenerationNo()
                        : null;
        String profileImageUrl =
                user != null
                        ? s3AssetUrlResolver.resolvePublicUrlOrNull(user.getProfileImageUrl())
                        : null;

        return RankingUserDto.of(
                userId,
                nickname,
                scoreDouble.longValue(),
                currentRank,
                cohortNo,
                profileImageUrl,
                rankDiff);
    }
}
