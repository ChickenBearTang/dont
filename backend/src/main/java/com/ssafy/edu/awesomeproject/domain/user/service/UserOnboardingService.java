package com.ssafy.edu.awesomeproject.domain.user.service;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.domain.auth.entity.OnboardingStatus;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.OnboardingStatusResponseDto;
import java.math.BigDecimal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserOnboardingService {
    private final UserRepository userRepository;

    public UserOnboardingService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public OnboardingStatusResponseDto getOnboardingStatus(Long userId) {
        User user = getUser(userId);
        OnboardingStatus onboardingStatus = user.getOnboardingStatusOrDefault();
        Long recommendedAmount =
                user.getMonthlySavingGoalAmount() == null
                        ? null
                        : user.getMonthlySavingGoalAmount().longValue();
        return new OnboardingStatusResponseDto(
                onboardingStatus.name(),
                onboardingStatus == OnboardingStatus.COMPLETED,
                recommendedAmount);
    }

    @Transactional
    public OnboardingStatusResponseDto saveOnboardingCheckpoint(
            Long userId, Long recommendedAmount) {
        User user = getUser(userId);
        user.updateMonthlySavingGoalAmount(BigDecimal.valueOf(recommendedAmount));
        user.markOnboardingInProgress();
        OnboardingStatus onboardingStatus = user.getOnboardingStatusOrDefault();
        Long savedRecommendedAmount =
                user.getMonthlySavingGoalAmount() == null
                        ? null
                        : user.getMonthlySavingGoalAmount().longValue();
        return new OnboardingStatusResponseDto(
                onboardingStatus.name(),
                onboardingStatus == OnboardingStatus.COMPLETED,
                savedRecommendedAmount);
    }

    @Transactional
    public OnboardingStatusResponseDto completeOnboarding(Long userId) {
        User user = getUser(userId);
        user.markOnboardingCompleted();
        OnboardingStatus onboardingStatus = user.getOnboardingStatusOrDefault();
        Long recommendedAmount =
                user.getMonthlySavingGoalAmount() == null
                        ? null
                        : user.getMonthlySavingGoalAmount().longValue();
        return new OnboardingStatusResponseDto(
                onboardingStatus.name(),
                onboardingStatus == OnboardingStatus.COMPLETED,
                recommendedAmount);
    }

    private User getUser(Long userId) {
        return userRepository
                .findById(userId)
                .orElseThrow(
                        () ->
                                new CommonException(
                                        CommonErrorCode.RESOURCE_NOT_FOUND, "사용자를 찾을 수 없습니다."));
    }
}
