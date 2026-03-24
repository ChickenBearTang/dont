package com.ssafy.edu.awesomeproject.domain.community.dto.response;

public record PostAttachmentResponseDto(
        Long attachmentId,
        String key,
        String fileName,
        String contentType,
        Long fileSize,
        String fileUrl) {}
