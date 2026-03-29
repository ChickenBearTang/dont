package com.ssafy.edu.awesomeproject.domain.ranking.service;

import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
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
    private final AccountRepository accountRepository;


    private static final String TOTAL_RANKING_KEY = "ranking:savebox:total";

    private static final String COHORT_RANKING_PREFIX = "ranking:savebox:cohort:";

    private static final double MAX_TIME_MS = 4102444800000.0;


    public void updateSaveboxRanking(Long userId, Long balance, Integer cohort) {
        long currentTimeMs = System.currentTimeMillis();


        double tieBreaker = 1.0 - (currentTimeMs / MAX_TIME_MS);
        double score = balance + tieBreaker;


        redisTemplate.opsForZSet().add(TOTAL_RANKING_KEY, String.valueOf(userId), score);


        if (cohort != null && cohort > 0) {
            String cohortKey = COHORT_RANKING_PREFIX + cohort;
            redisTemplate.opsForZSet().add(cohortKey, String.valueOf(userId), score);
        }
    }


    @Scheduled(cron = "1 0 0 * * *")
    public void createDailyRankingSnapshot() {
        log.info("[Ranking Snapshot] Starting daily ranking snapshot creation...");
        saveSnapshot(TOTAL_RANKING_KEY, "ranking:snapshot:total");


    }

    private void saveSnapshot(String sourceKey, String snapshotKey) {
        Set<String> range = redisTemplate.opsForZSet().reverseRange(sourceKey, 0, -1);
        if (range == null || range.isEmpty())
            return;

        redisTemplate.delete(snapshotKey);
        int rank = 1;
        for (String userId : range) {
            redisTemplate.opsForHash().put(snapshotKey, userId, String.valueOf(rank++));
        }
        log.info("[Ranking Snapshot] Saved snapshot to {} (count: {})", snapshotKey, range.size());
    }


    public List<RankingUserDto> getTop100Ranking(Integer cohort) {
        String key = (cohort != null && cohort > 0) ? COHORT_RANKING_PREFIX + cohort : TOTAL_RANKING_KEY;
        String snapshotKey = (cohort != null && cohort > 0)
                ? "ranking:snapshot:cohort:" + cohort
                : "ranking:snapshot:total";


        if (Boolean.FALSE.equals(redisTemplate.hasKey(snapshotKey))) {
            log.info(
                    "[Ranking Snapshot] Snapshot not found for {}. Creating initial snapshot...",
                    snapshotKey);
            saveSnapshot(key, snapshotKey);
        }

        Set<TypedTuple<String>> top100 = redisTemplate.opsForZSet().reverseRangeWithScores(key, 0, 99);

        if (top100 == null || top100.isEmpty())
            return List.of();

        long currentRank = 1;
        List<RankingUserDto> result = new ArrayList<>();
        List<Long> userIds = new ArrayList<>();
        List<Double> scores = new ArrayList<>();

        for (TypedTuple<String> tuple : top100) {
            Long id = Long.valueOf(tuple.getValue());
            Double score = tuple.getScore();
            if (score != null) {
                userIds.add(id);
                scores.add(score);
            }
        }


        Map<Long, User> userMap = userRepository.findAllById(userIds).stream()
                .collect(Collectors.toMap(User::getId, u -> u));


        Map<Object, Object> snapshotMap = redisTemplate.opsForHash().entries(snapshotKey);

        for (int i = 0; i < userIds.size(); i++) {
            Long userId = userIds.get(i);
            User user = userMap.get(userId);
            String nickname = user != null ? user.getNickname() : "탈퇴한 유저";


            Integer rankDiff = null;
            if (!snapshotMap.isEmpty() && snapshotMap.containsKey(userId.toString())) {
                try {
                    long lastRank = Long.parseLong(snapshotMap.get(userId.toString()).toString());
                    rankDiff = (int) (lastRank - currentRank);
                } catch (NumberFormatException ignored) {
                }
            }

            Integer cohortNo = (user != null && user.getCohort() != null)
                    ? user.getCohort().getGenerationNo()
                    : null;
            String profileImageUrl = user != null
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


    public RankingUserDto getMyRanking(Long userId, Integer cohort) {
        String key = (cohort != null && cohort > 0) ? COHORT_RANKING_PREFIX + cohort : TOTAL_RANKING_KEY;
        String userIdStr = String.valueOf(userId);

        Double scoreDouble = redisTemplate.opsForZSet().score(key, userIdStr);
        Long rank = redisTemplate.opsForZSet().reverseRank(key, userIdStr);

        if (scoreDouble == null || rank == null) {
            return RankingUserDto.of(userId, null, 0L, -1L, null, null, 0);
        }

        User user = userRepository.findById(userId).orElse(null);
        String nickname = user != null ? user.getNickname() : "탈퇴한 유저";


        String snapshotKey = (cohort != null && cohort > 0)
                ? "ranking:snapshot:cohort:" + cohort
                : "ranking:snapshot:total";


        if (Boolean.FALSE.equals(redisTemplate.hasKey(snapshotKey))) {
            saveSnapshot(key, snapshotKey);
        }

        Object lastRankObj = redisTemplate.opsForHash().get(snapshotKey, userIdStr);
        Integer rankDiff = null;
        long currentRank = rank + 1;
        if (lastRankObj != null) {
            try {
                long lastRank = Long.parseLong(lastRankObj.toString());
                rankDiff = (int) (lastRank - currentRank);
            } catch (NumberFormatException ignored) {
            }
        }

        Integer cohortNo = (user != null && user.getCohort() != null)
                ? user.getCohort().getGenerationNo()
                : null;
        String profileImageUrl = user != null
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


    @Transactional
    public void syncRankingFromDb() {
        log.info("[Ranking Sync] Starting atomic ranking synchronization...");

        List<User> activeUsers = userRepository.findAllByStatus(
                com.ssafy.edu.awesomeproject.domain.auth.entity.UserStatus.ACTIVE);

        if (activeUsers.isEmpty()) {
            log.warn("[Ranking Sync] No active users found in DB.");
            return;
        }

        var accounts = accountRepository.findAllByAccountRole(
                com.ssafy.edu.awesomeproject.domain.fin.account.entity.AccountRole.SAVE_BOX);

        Map<Long, java.math.BigDecimal> balanceMap = accounts.stream()
                .collect(Collectors.toMap(
                        com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account::getUserId,
                        com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account::getBalance,
                        java.math.BigDecimal::add));


        String tempTotalKey = TOTAL_RANKING_KEY + ":temp:" + System.currentTimeMillis();
        String tempCohortPrefix = COHORT_RANKING_PREFIX + "temp:" + System.currentTimeMillis() + ":";

        long currentTimeMs = System.currentTimeMillis();
        double tieBreaker = 1.0 - (currentTimeMs / MAX_TIME_MS);


        for (User user : activeUsers) {
            Long userId = user.getId();
            java.math.BigDecimal balance = balanceMap.getOrDefault(userId, java.math.BigDecimal.ZERO);
            double score = balance.longValue() + tieBreaker;

            redisTemplate.opsForZSet().add(tempTotalKey, String.valueOf(userId), score);

            if (user.getCohort() != null) {
                Integer cohortNo = user.getCohort().getGenerationNo();
                String tempCohortKey = tempCohortPrefix + cohortNo;
                redisTemplate.opsForZSet().add(tempCohortKey, String.valueOf(userId), score);
            }
        }


        redisTemplate.rename(tempTotalKey, TOTAL_RANKING_KEY);


        Set<String> oldCohortKeys = redisTemplate.keys(COHORT_RANKING_PREFIX + "*");
        if (oldCohortKeys != null) {

            oldCohortKeys.removeIf(k -> k.startsWith(tempCohortPrefix));
            if (!oldCohortKeys.isEmpty())
                redisTemplate.delete(oldCohortKeys);
        }

        Set<String> newTempCohortKeys = redisTemplate.keys(tempCohortPrefix + "*");
        if (newTempCohortKeys != null) {
            for (String tempKey : newTempCohortKeys) {
                String realKey = COHORT_RANKING_PREFIX + tempKey.substring(tempCohortPrefix.length());
                redisTemplate.rename(tempKey, realKey);
            }
        }

        log.info("[Ranking Sync] Atomic sync complete. Total Users: {}", activeUsers.size());
    }
}
