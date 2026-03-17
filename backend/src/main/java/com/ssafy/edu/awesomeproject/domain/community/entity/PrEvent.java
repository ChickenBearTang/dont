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
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "pr_events")
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PrEvent extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "post_id", nullable = false)
    private Long postId;

    @Column(name = "actor_user_id")
    private Long actorUserId;

    @Enumerated(EnumType.STRING)
    @Column(name = "event_type", nullable = false, length = 40)
    private PrEventType eventType;

    @Column(name = "payload", columnDefinition = "TEXT")
    private String payload;

    public PrEvent(Long postId, Long actorUserId, PrEventType eventType, String payload) {
        this.postId = postId;
        this.actorUserId = actorUserId;
        this.eventType = eventType;
        this.payload = payload;
    }
}
