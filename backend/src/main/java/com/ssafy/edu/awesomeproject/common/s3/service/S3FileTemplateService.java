package com.ssafy.edu.awesomeproject.common.s3.service;

import com.ssafy.edu.awesomeproject.common.config.S3Properties;
import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateDownloadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlsRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.UploadFileCommand;
import com.ssafy.edu.awesomeproject.common.s3.dto.response.PresignedUrlResponse;
import com.ssafy.edu.awesomeproject.common.s3.model.FileVisibility;
import java.util.List;
import java.util.Locale;
import org.springframework.stereotype.Service;

@Service
public class S3FileTemplateService {

    private final S3PresignService s3PresignService;
    private final S3Properties s3Properties;

    public S3FileTemplateService(S3PresignService s3PresignService, S3Properties s3Properties) {
        this.s3PresignService = s3PresignService;
        this.s3Properties = s3Properties;
    }

    public PresignedUrlResponse createPublicUploadUrl(
            String purpose, UploadFileCommand file, Integer expiresInSeconds) {
        return createUploadUrl(purpose, FileVisibility.PUBLIC, file, expiresInSeconds);
    }

    public PresignedUrlResponse createPrivateUploadUrl(
            String purpose, UploadFileCommand file, Integer expiresInSeconds) {
        return createUploadUrl(purpose, FileVisibility.PRIVATE, file, expiresInSeconds);
    }

    public PresignedUrlResponse createUploadUrl(
            String purpose,
            FileVisibility visibility,
            UploadFileCommand file,
            Integer expiresInSeconds) {
        validatePurpose(purpose);
        validateFile(file);

        return s3PresignService.createUploadUrl(
                new CreateUploadPresignedUrlRequest(
                        purpose,
                        visibility,
                        file.fileName(),
                        file.contentType(),
                        file.contentLength(),
                        expiresInSeconds));
    }

    public List<PresignedUrlResponse> createPublicUploadUrls(
            String purpose, List<UploadFileCommand> files, Integer expiresInSeconds) {
        return createUploadUrls(purpose, FileVisibility.PUBLIC, files, expiresInSeconds);
    }

    public List<PresignedUrlResponse> createPrivateUploadUrls(
            String purpose, List<UploadFileCommand> files, Integer expiresInSeconds) {
        return createUploadUrls(purpose, FileVisibility.PRIVATE, files, expiresInSeconds);
    }

    public List<PresignedUrlResponse> createUploadUrls(
            String purpose,
            FileVisibility visibility,
            List<UploadFileCommand> files,
            Integer expiresInSeconds) {
        validatePurpose(purpose);
        if (files == null || files.isEmpty()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "files는 비어 있을 수 없습니다.");
        }

        List<CreateUploadPresignedUrlRequest> requests =
                files.stream()
                        .peek(this::validateFile)
                        .map(
                                file ->
                                        new CreateUploadPresignedUrlRequest(
                                                purpose,
                                                visibility,
                                                file.fileName(),
                                                file.contentType(),
                                                file.contentLength(),
                                                expiresInSeconds))
                        .toList();

        return s3PresignService.createUploadUrls(new CreateUploadPresignedUrlsRequest(requests));
    }

    public PresignedUrlResponse createPrivateDownloadUrl(
            String key, String downloadFileName, Integer expiresInSeconds) {
        return s3PresignService.createDownloadUrl(
                new CreateDownloadPresignedUrlRequest(
                        key, FileVisibility.PRIVATE, downloadFileName, expiresInSeconds));
    }

    public String buildPublicObjectUrl(String key) {
        if (key == null || key.isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "key는 필수입니다.");
        }

        return String.format(
                Locale.ROOT,
                "https://%s.s3.%s.amazonaws.com/%s",
                s3Properties.getBucket(),
                s3Properties.getRegion(),
                key);
    }

    private void validatePurpose(String purpose) {
        if (purpose == null || purpose.isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "purpose는 필수입니다.");
        }
    }

    private void validateFile(UploadFileCommand file) {
        if (file == null) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "file은 null일 수 없습니다.");
        }
        if (file.fileName() == null || file.fileName().isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "fileName은 필수입니다.");
        }
        if (file.contentType() == null || file.contentType().isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "contentType은 필수입니다.");
        }
        if (file.contentLength() == null || file.contentLength() <= 0) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "contentLength는 0보다 커야 합니다.");
        }
    }
}
