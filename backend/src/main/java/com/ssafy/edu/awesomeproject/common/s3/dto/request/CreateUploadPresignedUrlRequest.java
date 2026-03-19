package com.ssafy.edu.awesomeproject.common.s3.dto.request;

import com.ssafy.edu.awesomeproject.common.s3.model.FileVisibility;

public record CreateUploadPresignedUrlRequest(
        String purpose,
        FileVisibility visibility,
        String fileName,
        String contentType,
        Long contentLength,
        Integer expiresInSeconds) {}
