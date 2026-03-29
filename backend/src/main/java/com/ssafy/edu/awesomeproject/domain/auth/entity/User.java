package com.ssafy.edu.awesomeproject.domain.auth.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "users")
@Getter
@Entity
@NoArgsConstructor(access = lombok.AccessLevel.PROTECTED)
public class User extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "email", nullable = false, unique = true, length = 255)
    private String email;

    @Column(name = "password", nullable = false, length = 255)
    private String password;

    @Column(name = "name", nullable = false, length = 50)
    private String name;

    @Column(name = "birth_date", nullable = false)
    private LocalDate birthDate;

    @Column(name = "nickname", length = 60)
    private String nickname;

    @Column(name = "profile_image_url")
    private String profileImageUrl;

    @Column(name = "ssafy_finance_user_key", length = 255)
    private String ssafyFinanceUserKey;

    @Column(name = "terms_agreed", nullable = false)
    private boolean termsAgreed;

    @Column(name = "terms_agreed_at")
    private LocalDateTime termsAgreedAt;

    @Column(name = "monthly_saving_goal_amount", precision = 15, scale = 2)
    private BigDecimal monthlySavingGoalAmount;

    @Enumerated(EnumType.STRING)
    @Column(name = "onboarding_status", length = 20)
    private OnboardingStatus onboardingStatus = OnboardingStatus.NOT_STARTED;

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false, length = 32)
    private UserRole userRole;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private UserStatus status = UserStatus.ACTIVE;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cohort_id", nullable = false)
    private Cohort cohort;

    public String getUserRole() {
        return userRole.toString();
    }

    public String getProfileImageUrl() {
        return profileImageUrl;
    }

    public OnboardingStatus getOnboardingStatusOrDefault() {
        return onboardingStatus != null ? onboardingStatus : OnboardingStatus.NOT_STARTED;
    }

    public void markOnboardingCompleted() {
        this.onboardingStatus = OnboardingStatus.COMPLETED;
    }

    public void markOnboardingInProgress() {
        this.onboardingStatus = OnboardingStatus.IN_PROGRESS;
    }

    public void updateMonthlySavingGoalAmount(BigDecimal monthlySavingGoalAmount) {
        this.monthlySavingGoalAmount = monthlySavingGoalAmount;
    }

    public void resetOnboarding() {
        this.onboardingStatus = OnboardingStatus.NOT_STARTED;
        this.monthlySavingGoalAmount = null;
    }

    public void changePassword(String encodedPassword) {
        this.password = encodedPassword;
    }

    public void changeNickname(String nickname) {
        this.nickname = nickname;
    }

    public void changeName(String name) {
        this.name = name;
    }

    public void changeBirthDate(LocalDate birthDate) {
        this.birthDate = birthDate;
    }

    public void changeProfileImageUrl(String profileImageUrl) {
        this.profileImageUrl = profileImageUrl;
    }

    public void updateSsafyFinanceUserKey(String ssafyFinanceUserKey) {
        this.ssafyFinanceUserKey = ssafyFinanceUserKey;
    }

    public void softDelete(LocalDateTime deletedAt) {
        this.status = UserStatus.DELETED;
        this.deletedAt = deletedAt;
    }

    public User(
            String email,
            String password,
            String name,
            LocalDate birthDate,
            String nickname,
            String profileImageUrl,
            boolean termsAgreed,
            LocalDateTime termsAgreedAt,
            UserRole userRole,
            Cohort cohort) {
        this.email = email;
        this.password = password;
        this.name = name;
        this.birthDate = birthDate;
        this.nickname = nickname;
        this.profileImageUrl = profileImageUrl;
        this.termsAgreed = termsAgreed;
        this.termsAgreedAt = termsAgreedAt;
        this.onboardingStatus = OnboardingStatus.NOT_STARTED;
        this.userRole = userRole;
        this.status = UserStatus.ACTIVE;
        this.deletedAt = null;
        this.cohort = cohort;
    }
}
