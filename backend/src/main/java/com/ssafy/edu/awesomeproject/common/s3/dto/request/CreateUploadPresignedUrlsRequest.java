package com.ssafy.edu.awesomeproject.common.s3.dto.request;

import java.util.List;

public record CreateUploadPresignedUrlsRequest(List<CreateUploadPresignedUrlRequest> files) {}
