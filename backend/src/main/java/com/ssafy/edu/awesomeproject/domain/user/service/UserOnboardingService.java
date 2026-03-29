package com.ssafy.edu.awesomeproject.domain.user.service;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.domain.auth.entity.OnboardingStatus;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.OnboardingStatusResponseDto;
import java.math.BigDecimal;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserOnboardingService {
    private final UserRepository userRepository;
    private final SavingsSettingRepository savingsSettingRepository;

    public UserOnboardingService(
            UserRepository userRepository, SavingsSettingRepository savingsSettingRepository) {
        this.userRepository = userRepository;
        this.savingsSettingRepository = savingsSettingRepository;
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

    @Transactional
    public void resetOnboarding(Long userId) {
        User user = getUser(userId);
        user.resetOnboarding();
        savingsSettingRepository.deleteAllByUserId(userId);
    }

    private User getUser(Long userId) {
        return userRepository
                .findActiveById(userId)
                .orElseThrow(
                        () ->
                                new CommonException(
                                        CommonErrorCode.RESOURCE_NOT_FOUND, "사용자를 찾을 수 없습니다."));
    }
}
