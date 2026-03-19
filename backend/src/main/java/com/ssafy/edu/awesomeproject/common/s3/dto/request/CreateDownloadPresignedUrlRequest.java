package com.ssafy.edu.awesomeproject.common.s3.dto.request;

import com.ssafy.edu.awesomeproject.common.s3.model.FileVisibility;

public record CreateDownloadPresignedUrlRequest(
        String key, FileVisibility visibility, String downloadFileName, Integer expiresInSeconds) {}
