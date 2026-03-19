package com.ssafy.edu.awesomeproject.domain.auth.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import jakarta.persistence.*;
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

    @Column(name = "nickname", nullable = false, length = 60)
    private String nickname;

    @Column(name = "profile_image_url")
    private String profileImageUrl;

    // 유저의 키를 받아오는용
    @Column(name = "ssafy_finance_user_key", length = 255)
    private String ssafyFinanceUserKey;

    @Column(name = "terms_agreed", nullable = false)
    private boolean termsAgreed;

    @Column(name = "terms_agreed_at")
    private LocalDateTime termsAgreedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false, length = 32)
    private UserRole userRole;

    // cohort 매핑을 위한 FK 조건 추가
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cohort_id", nullable = false)
    private Cohort cohort;

    public String getUserRole() {
        return userRole.toString();
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
        this.userRole = userRole;
        this.cohort = cohort;
    }
}
