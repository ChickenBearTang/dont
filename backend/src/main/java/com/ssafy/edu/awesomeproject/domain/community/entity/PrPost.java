package com.ssafy.edu.awesomeproject.domain.community.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
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

@Table(name = "pr_posts")
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class PrPost {

    @Id
    @Column(name = "post_id", nullable = false)
    private Long postId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private Post post;

    @Column(name = "item_name", nullable = false, length = 200)
    private String itemName;

    @Column(name = "price_amount", nullable = false)
    private Long priceAmount;

    @Column(name = "category", length = 200)
    private String category;

    @Column(name = "purchase_url", columnDefinition = "TEXT")
    private String purchaseUrl;

    @Column(name = "image_url", length = 255)
    private String imageUrl;

    @Column(name = "deadline_at")
    private LocalDateTime deadlineAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "close_reason", length = 30)
    private PrCloseReason closeReason;

    @Column(name = "closed_at")
    private LocalDateTime closedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "result_status", nullable = false, length = 20)
    private PrStatus resultStatus;

    public Long getPostId() {
        return postId;
    }

    public String getResultStatus() {
        return resultStatus.toString();
    }

    public PrStatus getResultStatusEnum() {
        return resultStatus;
    }

    public PrPost(
            Post post,
            String itemName,
            Long priceAmount,
            String category,
            String purchaseUrl,
            String imageUrl,
            LocalDateTime deadlineAt) {
        this.post = post;
        this.itemName = itemName;
        this.priceAmount = priceAmount;
        this.category = category;
        this.purchaseUrl = purchaseUrl;
        this.imageUrl = imageUrl;
        this.deadlineAt = deadlineAt;
        this.resultStatus = PrStatus.OPEN;
    }

    public void close(PrStatus resultStatus, PrCloseReason closeReason) {
        this.resultStatus = resultStatus;
        this.closeReason = closeReason;
        this.closedAt = LocalDateTime.now();
    }
}
