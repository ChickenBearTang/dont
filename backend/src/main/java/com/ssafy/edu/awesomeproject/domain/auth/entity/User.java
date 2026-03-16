package com.ssafy.edu.awesomeproject.domain.auth.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.community.entity.Cohort;
import jakarta.persistence.*;
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

    // TODO : nullable=false로 변경해야함. 작업 속도 증진을 위해서 우선 null로 둠(회원가입 시 매번 이름을 입력하는 것이 번거로움)
    @Column(name = "name", length = 32)
    private String name;

    @Column(name = "nickname", length = 16)
    private String nickname;

    @Column(name = "profile_image_url")
    private String profileImageUrl;

    //유저의 키를 받아오는용
    @Column(name = "ssafy_finance_user_key", length = 255)
    private String ssafyFinanceUserKey;

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false, length = 32)
    private UserRole userRole;

    //cohort 매핑을 위한 FK 조건 추가
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cohort_id")
    private Cohort cohort;

    public String getUserRole() {
        return userRole.toString();
    }

    public User(
            String email,
            String password,
            String name,
            String nickname,
            String profileImageUrl,
            UserRole userRole,
            Cohort cohort) {
        this.email = email;
        this.password = password;
        this.name = name;
        this.nickname = nickname;
        this.profileImageUrl = profileImageUrl;
        this.userRole = userRole;
        this.cohort = cohort;
    }
}
