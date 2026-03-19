package com.ssafy.edu.awesomeproject.common.s3.service;

import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateDownloadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlsRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.response.PresignedUrlResponse;
import java.util.List;

public interface S3PresignService {

    PresignedUrlResponse createUploadUrl(CreateUploadPresignedUrlRequest request);

    List<PresignedUrlResponse> createUploadUrls(CreateUploadPresignedUrlsRequest request);

    PresignedUrlResponse createDownloadUrl(CreateDownloadPresignedUrlRequest request);
}
