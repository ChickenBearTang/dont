package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record PrCreateRequestDto(
        @NotBlank @Size(max = 200) String title,
        @NotBlank String content,
        @NotBlank @Size(max = 200) String itemName,
        @NotNull @Positive @Min(1000) Long priceAmount,
        @Size(max = 200) String category,
        @Pattern(regexp = "^(https?://)\\S+$") String purchaseUrl,
        @Size(max = 255) String imageUrl,
        @Future LocalDateTime deadlineAt) {}
