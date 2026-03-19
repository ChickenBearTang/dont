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

@Table(name = "hotdeal_posts")
@Getter
@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class HotdealPost {

    @Id
    @Column(name = "post_id", nullable = false)
    private Long postId;

    @MapsId
    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "post_id", nullable = false)
    private Post post;

    @Column(name = "product_name", nullable = false, length = 200)
    private String productName;

    @Column(name = "store_name", length = 100)
    private String storeName;

    @Column(name = "deal_price_amount", nullable = false)
    private Long dealPriceAmount;

    @Column(name = "original_price_amount")
    private Long originalPriceAmount;

    @Column(name = "deal_url", columnDefinition = "TEXT")
    private String dealUrl;

    @Column(name = "shipping_info", length = 255)
    private String shippingInfo;

    @Column(name = "expired_at")
    private LocalDateTime expiredAt;

    public HotdealPost(
            Post post,
            String productName,
            String storeName,
            Long dealPriceAmount,
            Long originalPriceAmount,
            String dealUrl,
            String shippingInfo,
            LocalDateTime expiredAt) {
        this.post = post;
        this.productName = productName;
        this.storeName = storeName;
        this.dealPriceAmount = dealPriceAmount;
        this.originalPriceAmount = originalPriceAmount;
        this.dealUrl = dealUrl;
        this.shippingInfo = shippingInfo;
        this.expiredAt = expiredAt;
    }

    public void update(
            String productName,
            String storeName,
            Long dealPriceAmount,
            Long originalPriceAmount,
            String dealUrl,
            String shippingInfo,
            LocalDateTime expiredAt) {
        if (productName != null && !productName.isBlank()) {
            this.productName = productName;
        }
        if (storeName != null) {
            this.storeName = storeName;
        }
        if (dealPriceAmount != null) {
            this.dealPriceAmount = dealPriceAmount;
        }
        if (originalPriceAmount != null) {
            this.originalPriceAmount = originalPriceAmount;
        }
        if (dealUrl != null) {
            this.dealUrl = dealUrl;
        }
        if (shippingInfo != null) {
            this.shippingInfo = shippingInfo;
        }
        if (expiredAt != null) {
            this.expiredAt = expiredAt;
        }
    }
}
