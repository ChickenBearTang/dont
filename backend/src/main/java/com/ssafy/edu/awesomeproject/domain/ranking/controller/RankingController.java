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
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/ranking")
@RequiredArgsConstructor
public class RankingController {

    private final RankingService rankingService;
    private final UserRepository userRepository;


    @GetMapping("/total")
    public CommonResponse<RankingListResponse> getTotalRanking(@CurrentUserId Long userId) {
        List<RankingUserDto> top100 = rankingService.getTop100Ranking(null);
        RankingUserDto myRanking = rankingService.getMyRanking(userId, null);

        return CommonResponse.success(RankingListResponse.of(top100, myRanking));
    }


    @GetMapping("/cohort")
    public CommonResponse<RankingListResponse> getCohortRanking(
            @CurrentUserId Long userId, @RequestParam(required = false) Integer cohortNo) {


        if (cohortNo == null) {
            User user =
                    userRepository
                            .findById(userId)
                            .orElseThrow(
                                    () ->
                                            new IllegalArgumentException(
                                                    "User not found: " + userId));
            cohortNo = (user.getCohort() != null) ? user.getCohort().getGenerationNo() : null;
        }

        List<RankingUserDto> top100 = rankingService.getTop100Ranking(cohortNo);
        RankingUserDto myRanking = rankingService.getMyRanking(userId, cohortNo);

        return CommonResponse.success(RankingListResponse.of(top100, myRanking));
    }


    @PostMapping("/sync")
    public CommonResponse<String> syncRanking(@CurrentUserId Long userId) {
        rankingService.syncRankingFromDb();
        return CommonResponse.success("Ranking synchronization completed successfully.");
    }
}
