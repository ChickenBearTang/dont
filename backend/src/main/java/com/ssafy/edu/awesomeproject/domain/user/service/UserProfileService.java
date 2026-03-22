package com.ssafy.edu.awesomeproject.domain.user.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.entity.UserStatus;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordHashService;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.MyPageUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.MyPageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.NicknameChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.PasswordChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.WithdrawResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.error.UserErrorCode;
import com.ssafy.edu.awesomeproject.domain.user.error.UserException;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.regex.Pattern;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserProfileService {
    private static final int NICKNAME_MIN_LENGTH = 2;
    private static final int NICKNAME_MAX_LENGTH = 20;
    private static final Pattern NICKNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9가-힣_]+$");

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final RefreshTokenStore refreshTokenStore;

    public UserProfileService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            RefreshTokenStore refreshTokenStore) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.refreshTokenStore = refreshTokenStore;
    }

    @Transactional(readOnly = true)
    public MyPageResponseDto getMyPage(Long userId) {
        User user = getUser(userId);
        return toMyPageResponse(user);
    }

    @Transactional
    public MyPageResponseDto updateMyPage(Long userId, MyPageUpdateRequestDto request) {
        User user = getUser(userId);

        if (request.name() == null
                && request.birthDate() == null
                && request.monthlySavingGoalAmount() == null) {
            throw new UserException(UserErrorCode.MY_PAGE_UPDATE_EMPTY);
        }

        if (request.name() != null) {
            String normalizedName = request.name().trim();
            if (normalizedName.isEmpty()) {
                throw new UserException(UserErrorCode.NAME_INVALID);
            }
            user.changeName(normalizedName);
        }

        if (request.birthDate() != null) {
            user.changeBirthDate(request.birthDate());
        }

        if (request.monthlySavingGoalAmount() != null) {
            user.updateMonthlySavingGoalAmount(
                    BigDecimal.valueOf(request.monthlySavingGoalAmount()));
        }

        return toMyPageResponse(user);
    }

    @Transactional
    public NicknameChangeResponseDto changeNickname(Long userId, String rawNickname) {
        User user = getUser(userId);
        String nickname = normalizeNickname(rawNickname);
        validateNickname(nickname);

        if (nickname.equals(user.getNickname())) {
            return new NicknameChangeResponseDto(user.getId(), user.getNickname());
        }

        ensureNicknameAvailable(nickname, userId);

        user.changeNickname(nickname);

        try {
            userRepository.flush();
        } catch (DataIntegrityViolationException exception) {
            throw new UserException(UserErrorCode.NICKNAME_ALREADY_EXISTS);
        }

        return new NicknameChangeResponseDto(user.getId(), user.getNickname());
    }

    @Transactional
    public PasswordChangeResponseDto changePassword(
            Long userId, String currentPassword, String newPassword) {
        User user = getUser(userId);

        if (!passwordHashService.matches(currentPassword, user.getPassword())) {
            throw new UserException(UserErrorCode.CURRENT_PASSWORD_MISMATCH);
        }

        if (passwordHashService.matches(newPassword, user.getPassword())) {
            throw new UserException(UserErrorCode.NEW_PASSWORD_SAME_AS_CURRENT);
        }

        user.changePassword(passwordHashService.encode(newPassword));
        refreshTokenStore.deleteByUserId(user.getId());

        return new PasswordChangeResponseDto(true, true);
    }

    @Transactional
    public WithdrawResponseDto withdraw(Long userId, String currentPassword) {
        User user = getUser(userId);

        if (!passwordHashService.matches(currentPassword, user.getPassword())) {
            throw new UserException(UserErrorCode.CURRENT_PASSWORD_MISMATCH);
        }

        user.softDelete(LocalDateTime.now());
        refreshTokenStore.deleteByUserId(user.getId());

        return new WithdrawResponseDto(true, true);
    }

    private User getUser(Long userId) {
        return userRepository
                .findByIdAndStatus(userId, UserStatus.ACTIVE)
                .orElseThrow(() -> new UserException(UserErrorCode.USER_NOT_FOUND));
    }

    private String normalizeNickname(String rawNickname) {
        return rawNickname == null ? "" : rawNickname.trim();
    }

    private void validateNickname(String nickname) {
        if (nickname.length() < NICKNAME_MIN_LENGTH || nickname.length() > NICKNAME_MAX_LENGTH) {
            throw new UserException(UserErrorCode.NICKNAME_INVALID_LENGTH);
        }

        if (!NICKNAME_PATTERN.matcher(nickname).matches()) {
            throw new UserException(UserErrorCode.NICKNAME_INVALID_FORMAT);
        }
    }

    private void ensureNicknameAvailable(String nickname, Long userId) {
        if (userRepository.existsByNicknameAndIdNot(nickname, userId)) {
            throw new UserException(UserErrorCode.NICKNAME_ALREADY_EXISTS);
        }
    }

    private MyPageResponseDto toMyPageResponse(User user) {
        Long monthlySavingGoalAmount =
                user.getMonthlySavingGoalAmount() == null
                        ? null
                        : user.getMonthlySavingGoalAmount().longValue();

        return new MyPageResponseDto(
                user.getId(),
                user.getEmail(),
                user.getName(),
                user.getNickname(),
                user.getBirthDate(),
                user.getProfileImageUrl(),
                user.getOnboardingStatusOrDefault().name(),
                monthlySavingGoalAmount,
                user.getCohort().getId(),
                user.getCohort().getGenerationNo());
    }
}
