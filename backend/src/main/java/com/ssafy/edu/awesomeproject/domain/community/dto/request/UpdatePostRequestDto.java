package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.util.List;


public record UpdatePostRequestDto(
        @NotBlank @Size(max = 200) String title,
        String content,
        List<@Valid PostAttachmentRequestDto> attachments) {}
