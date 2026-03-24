package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record HotdealUpdateRequestDto(
        @Size(max = 200) String title,
        String content,
        @Size(max = 200) String productName,
        @Size(max = 100) String storeName,
        @Positive Long dealPriceAmount,
        @Positive Long originalPriceAmount,
        @Size(max = 2000) String dealUrl,
        @Size(max = 255) String shippingInfo,
        LocalDateTime expiredAt,
        List<@Valid PostAttachmentRequestDto> attachments) {}
