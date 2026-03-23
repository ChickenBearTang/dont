package com.ssafy.edu.awesomeproject.domain.user.service;

import com.ssafy.edu.awesomeproject.common.s3.dto.request.UploadFileCommand;
import com.ssafy.edu.awesomeproject.common.s3.dto.response.PresignedUrlResponse;
import com.ssafy.edu.awesomeproject.common.s3.error.S3ErrorCode;
import com.ssafy.edu.awesomeproject.common.s3.error.S3Exception;
import com.ssafy.edu.awesomeproject.common.s3.service.S3AssetUrlResolver;
import com.ssafy.edu.awesomeproject.common.s3.service.S3FileTemplateService;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.auth.service.DefaultProfileImagePolicy;
import com.ssafy.edu.awesomeproject.domain.auth.service.PasswordHashService;
import com.ssafy.edu.awesomeproject.domain.auth.token.RefreshTokenStore;
import com.ssafy.edu.awesomeproject.domain.user.dto.request.MyPageUpdateRequestDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.MyPageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.NicknameChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.PasswordChangeResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImageDeleteResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImagePresignResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.ProfileImageResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.dto.response.WithdrawResponseDto;
import com.ssafy.edu.awesomeproject.domain.user.error.UserErrorCode;
import com.ssafy.edu.awesomeproject.domain.user.error.UserException;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class UserProfileService {
    private static final int NICKNAME_MIN_LENGTH = 2;
    private static final int NICKNAME_MAX_LENGTH = 20;
    private static final Pattern NICKNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9가-힣_]+$");
    private static final Set<String> ALLOWED_PROFILE_CONTENT_TYPES =
            Set.of("image/jpeg", "image/png", "image/webp");
    private static final Set<String> ALLOWED_PROFILE_EXTENSIONS =
            Set.of("jpg", "jpeg", "png", "webp");
    private static final String PROFILE_IMAGE_PURPOSE_PREFIX = "profile-user-";

    private final UserRepository userRepository;
    private final PasswordHashService passwordHashService;
    private final RefreshTokenStore refreshTokenStore;
    private final DefaultProfileImagePolicy defaultProfileImagePolicy;
    private final S3FileTemplateService s3FileTemplateService;
    private final S3AssetUrlResolver s3AssetUrlResolver;

    public UserProfileService(
            UserRepository userRepository,
            PasswordHashService passwordHashService,
            RefreshTokenStore refreshTokenStore,
            DefaultProfileImagePolicy defaultProfileImagePolicy,
            S3FileTemplateService s3FileTemplateService,
            S3AssetUrlResolver s3AssetUrlResolver) {
        this.userRepository = userRepository;
        this.passwordHashService = passwordHashService;
        this.refreshTokenStore = refreshTokenStore;
        this.defaultProfileImagePolicy = defaultProfileImagePolicy;
        this.s3FileTemplateService = s3FileTemplateService;
        this.s3AssetUrlResolver = s3AssetUrlResolver;
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

    @Transactional(readOnly = true)
    public ProfileImagePresignResponseDto createProfileImageUploadUrl(
            Long userId, String fileName, String contentType, Long contentLength) {
        getUser(userId);
        validateProfileImageFile(fileName, contentType);

        PresignedUrlResponse presignedUrlResponse =
                s3FileTemplateService.createPublicUploadUrl(
                        buildProfileImagePurpose(userId),
                        new UploadFileCommand(fileName, contentType, contentLength),
                        null);

        return new ProfileImagePresignResponseDto(
                presignedUrlResponse.url(),
                presignedUrlResponse.method(),
                presignedUrlResponse.headers(),
                presignedUrlResponse.key(),
                presignedUrlResponse.expiresAt(),
                s3AssetUrlResolver.resolvePublicUrlOrNull(presignedUrlResponse.key()));
    }

    @Transactional
    public ProfileImageResponseDto completeProfileImageUpload(Long userId, String key) {
        User user = getUser(userId);
        String normalizedKey = normalizeKey(key);
        validateProfileImageKey(userId, normalizedKey);

        user.changeProfileImageUrl(normalizedKey);
        return new ProfileImageResponseDto(
                normalizedKey, s3AssetUrlResolver.resolvePublicUrlOrNull(normalizedKey));
    }

    @Transactional
    public ProfileImageDeleteResponseDto deleteProfileImage(Long userId) {
        User user = getUser(userId);
        String defaultProfileImageKey = defaultProfileImagePolicy.pickRandomKey();
        user.changeProfileImageUrl(defaultProfileImageKey);

        return new ProfileImageDeleteResponseDto(
                true,
                defaultProfileImageKey,
                s3AssetUrlResolver.resolvePublicUrlOrNull(defaultProfileImageKey));
    }

    private User getUser(Long userId) {
        return userRepository
                .findActiveById(userId)
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

    private void validateProfileImageFile(String fileName, String contentType) {
        String normalizedContentType = contentType.toLowerCase(Locale.ROOT);
        if (!ALLOWED_PROFILE_CONTENT_TYPES.contains(normalizedContentType)) {
            throw new S3Exception(S3ErrorCode.INVALID_CONTENT_TYPE);
        }

        String extension = extractExtension(fileName);
        if (!ALLOWED_PROFILE_EXTENSIONS.contains(extension)) {
            throw new S3Exception(S3ErrorCode.INVALID_FILE_NAME);
        }
    }

    private String extractExtension(String fileName) {
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex < 0 || dotIndex == fileName.length() - 1) {
            throw new S3Exception(S3ErrorCode.INVALID_FILE_NAME);
        }
        return fileName.substring(dotIndex + 1).toLowerCase(Locale.ROOT);
    }

    private void validateProfileImageKey(Long userId, String key) {
        String expectedPrefix = "public/profile/" + userId + "/";
        if (!key.startsWith(expectedPrefix)) {
            throw new S3Exception(S3ErrorCode.INVALID_OBJECT_KEY);
        }
    }

    private String buildProfileImagePurpose(Long userId) {
        return PROFILE_IMAGE_PURPOSE_PREFIX + userId;
    }

    private String normalizeKey(String key) {
        return key == null ? "" : key.trim();
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
                s3AssetUrlResolver.resolvePublicUrlOrNull(user.getProfileImageUrl()),
                user.getOnboardingStatusOrDefault().name(),
                monthlySavingGoalAmount,
                user.getCohort().getId(),
                user.getCohort().getGenerationNo());
    }
}
