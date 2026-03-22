package com.ssafy.edu.awesomeproject.domain.user.service;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.MyPageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.NicknameChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.error.UserErrorCode;
import com.ssafy.edu.awesomeproject.domain.user.error.UserException;
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

    public UserProfileService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Transactional(readOnly = true)
    public MyPageResponseDto getMyPage(Long userId) {
        User user = getUser(userId);
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

    private User getUser(Long userId) {
        return userRepository
                .findById(userId)
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
}
