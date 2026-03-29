package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "comments")
@Getter
@Entity
@NoArgsConstructor(access = lombok.AccessLevel.PROTECTED)
public class Comment extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private Post post;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_comment_id")
    private Comment parentComment;

    @Column(name = "content", nullable = false, columnDefinition = "TEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private CommentStatus status;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    public Comment(Post post, User user, Comment parentComment, String content) {
        this.post = post;
        this.user = user;
        this.parentComment = parentComment;
        this.content = content;
        this.status = CommentStatus.ACTIVE;
        this.deletedAt = null;
    }

    public void update(String content) {
        if (content != null && !content.isBlank()) {
            this.content = content;
        }
    }

    public void delete() {
        this.status = CommentStatus.DELETED;
        this.deletedAt = LocalDateTime.now();
    }


    public void blind() {
        this.status = CommentStatus.BLINDED;
    }

    public boolean isAuthor(Long userId) {
        return this.user.getId().equals(userId);
    }

    public boolean isChildComment() {
        return this.parentComment != null;
    }
}
