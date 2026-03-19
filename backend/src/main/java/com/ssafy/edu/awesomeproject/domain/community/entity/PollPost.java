package com.ssafy.edu.awesomeproject.domain.community.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.MapsId;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "poll_posts")
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PollPost {

    @Id
    @Column(name = "post_id", nullable = false)
    private Long postId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private Post post;

    @Column(name = "question", nullable = false, length = 255)
    private String question;

    @Column(name = "option_a", nullable = false, length = 255)
    private String optionA;

    @Column(name = "option_b", nullable = false, length = 255)
    private String optionB;

    @Column(name = "deadline_at")
    private LocalDateTime deadlineAt;

    public PollPost(
            Post post, String question, String optionA, String optionB, LocalDateTime deadlineAt) {
        this.post = post;
        this.question = question;
        this.optionA = optionA;
        this.optionB = optionB;
        this.deadlineAt = deadlineAt;
    }

    public void update(String question, String optionA, String optionB, LocalDateTime deadlineAt) {
        if (question != null && !question.isBlank()) {
            this.question = question;
        }
        if (optionA != null && !optionA.isBlank()) {
            this.optionA = optionA;
        }
        if (optionB != null && !optionB.isBlank()) {
            this.optionB = optionB;
        }
        if (deadlineAt != null) {
            this.deadlineAt = deadlineAt;
        }
    }

    public boolean isClosed(LocalDateTime now) {
        return deadlineAt != null && !deadlineAt.isAfter(now);
    }
}
