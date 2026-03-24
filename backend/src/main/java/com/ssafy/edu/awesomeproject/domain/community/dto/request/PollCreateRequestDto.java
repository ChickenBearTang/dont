package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Future;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record PollCreateRequestDto(
        @NotBlank @Size(max = 200) String title,
        @NotBlank String content,
        @NotBlank @Size(max = 255) String question,
        @NotBlank @Size(max = 255) String optionA,
        @NotBlank @Size(max = 255) String optionB,
        @NotNull @Future LocalDateTime deadlineAt,
        List<@Valid PostAttachmentRequestDto> attachments) {}
