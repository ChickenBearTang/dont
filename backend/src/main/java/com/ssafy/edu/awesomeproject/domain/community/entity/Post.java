package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "posts")
@Getter
@Entity
@NoArgsConstructor(access = lombok.AccessLevel.PROTECTED)
public class Post extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "board_id", nullable = false)
    private Board board;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "title", nullable = false, length = 200)
    private String title;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Column(name = "is_system_generated", nullable = false)
    private Boolean isSystemGenerated;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private PostStatus status;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    // 게시글(post) 기본 상태
    public Post(Board board, User user, String title, String content) {
        this.title = title;
        this.content = content;
        this.board = board;
        this.user = user;
        this.deletedAt = null;
        this.isSystemGenerated = false;
        this.status = PostStatus.ACTIVE;
    }

    // title이 비어있지 않고 content도 비어있지 않으면
    // table에 not null 설정
    // update 가능
    public void update(String title, String content) {
        if (title != null && !title.isEmpty()) {
            this.title = title;
        }
        if (content != null && !content.isEmpty()) {
            this.content = content;
        }
    }

    public void delete() {
        this.status = PostStatus.DELETED;
        this.deletedAt = LocalDateTime.now();
    }

    // 사용자가 맞는지 확인
    public boolean isAuthor(Long userId) {
        return this.user.getId().equals(userId);
    }
}
