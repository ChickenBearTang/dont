package com.ssafy.edu.awesomeproject.domain.ranking.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingListResponse;
import com.ssafy.edu.awesomeproject.domain.ranking.dto.response.RankingUserDto;
import com.ssafy.edu.awesomeproject.domain.ranking.service.RankingService;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/ranking")
@RequiredArgsConstructor
public class RankingController {

    private final RankingService rankingService;
    private final UserRepository userRepository;

    /** 전체 세이브박스 랭킹 Top 10 및 내 랭킹 조회 */
    @GetMapping("/total")
    public CommonResponse<RankingListResponse> getTotalRanking(@CurrentUserId Long userId) {
        List<RankingUserDto> top10 = rankingService.getTop10Ranking(null);
        RankingUserDto myRanking = rankingService.getMyRanking(userId, null);

        return CommonResponse.success(RankingListResponse.of(top10, myRanking));
    }

    /** 기수(Cohort)별 세이브박스 랭킹 Top 10 및 내 랭킹 조회 */
    @GetMapping("/cohort")
    public CommonResponse<RankingListResponse> getCohortRanking(@CurrentUserId Long userId) {
        User user =
                userRepository
                        .findById(userId)
                        .orElseThrow(
                                () -> new IllegalArgumentException("User not found: " + userId));

        // 유저 엔티티의 Lazy 로딩된 Cohort 객체에서 기수 번호를 안전하게 추출
        Integer cohortNo = (user.getCohort() != null) ? user.getCohort().getGenerationNo() : null;

        List<RankingUserDto> top10 = rankingService.getTop10Ranking(cohortNo);
        RankingUserDto myRanking = rankingService.getMyRanking(userId, cohortNo);

        return CommonResponse.success(RankingListResponse.of(top10, myRanking));
    }
}
