package com.ssafy.edu.awesomeproject.domain.community.entity;

import com.ssafy.edu.awesomeproject.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(
        name = "pr_votes",
        uniqueConstraints =
                @UniqueConstraint(
                        name = "uk_pr_votes_post_user",
                        columnNames = {"post_id", "user_id"}))
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PrVote extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "post_id", nullable = false)
    private Long postId;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Enumerated(EnumType.STRING)
    @Column(name = "vote_value", nullable = false, length = 20)
    private PrVoteValue voteValue;

    @Column(name = "opinion_text", columnDefinition = "TEXT")
    private String opinionText;

    public PrVote(Long postId, Long userId, PrVoteValue voteValue, String opinionText) {
        this.postId = postId;
        this.userId = userId;
        this.voteValue = voteValue;
        this.opinionText = opinionText;
    }
}
