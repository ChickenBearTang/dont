package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Future;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.List;

public record PollUpdateRequestDto(
        @Size(max = 200) String title,
        String content,
        @Size(max = 255) String question,
        @Size(max = 255) String optionA,
        @Size(max = 255) String optionB,
        @Future LocalDateTime deadlineAt,
        List<@Valid PostAttachmentRequestDto> attachments) {}
