package com.ssafy.edu.awesomeproject.domain.auth.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
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

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false, length = 32)
    private UserRole userRole;

    public String getUserRole() {
        return userRole.toString();
    }

    public User(
            String email,
            String password,
            String name,
            String nickname,
            String profileImageUrl,
            UserRole userRole) {
        this.email = email;
        this.password = password;
        this.name = name;
        this.nickname = nickname;
        this.profileImageUrl = profileImageUrl;
        this.userRole = userRole;
    }
}
