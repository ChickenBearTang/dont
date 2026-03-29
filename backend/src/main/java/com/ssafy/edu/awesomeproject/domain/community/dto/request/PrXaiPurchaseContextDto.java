package com.ssafy.edu.awesomeproject.domain.community.dto.request;

public record PrXaiPurchaseContextDto(
        Long postId,
        String title,
        String itemName,
        String content,
        String category,
        String purchaseUrl,
        PrXaiProvenanceValueDto priceAmount) {}
