package com.ssafy.edu.awesomeproject.domain.community.dto.request;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import java.util.List;

public record AttachmentPresignRequestDto(@NotEmpty List<@Valid AttachmentPresignFileRequestDto> files) {}
