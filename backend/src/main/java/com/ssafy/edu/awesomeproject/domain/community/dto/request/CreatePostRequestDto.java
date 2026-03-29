package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import com.ssafy.edu.awesomeproject.domain.community.entity.BoardCategory;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;


public record CreatePostRequestDto(
        @NotNull BoardCategory category,
        Integer generationNo,
        @NotNull @Size(max = 200) String title,
        @NotNull String content,
        List<@Valid PostAttachmentRequestDto> attachments) {}
