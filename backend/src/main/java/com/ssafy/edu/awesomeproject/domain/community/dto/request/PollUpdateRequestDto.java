package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;

public record PollUpdateRequestDto(
        @Size(max = 200) String title,
        String content,
        @Size(max = 255) String question,
        @Size(max = 255) String optionA,
        @Size(max = 255) String optionB,
        @Future LocalDateTime deadlineAt) {}
