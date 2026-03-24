package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Future;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record PrCreateRequestDto(
        @NotBlank @Size(max = 200) String title,
        @NotBlank String content,
        @NotBlank @Size(max = 200) String itemName,
        @NotNull @PositiveOrZero Long priceAmount,
        @Size(max = 200) String category,
        @Pattern(regexp = "^(https?://)\\S+$") String purchaseUrl,
        @Future LocalDateTime deadlineAt,
        List<@Valid PostAttachmentRequestDto> attachments) {}
