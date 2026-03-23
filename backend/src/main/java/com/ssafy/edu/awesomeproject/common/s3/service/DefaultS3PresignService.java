package com.ssafy.edu.awesomeproject.common.s3.service;

import com.ssafy.edu.awesomeproject.common.config.S3Properties;
import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateDownloadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.request.CreateUploadPresignedUrlsRequest;
import com.ssafy.edu.awesomeproject.common.s3.dto.response.PresignedUrlResponse;
import com.ssafy.edu.awesomeproject.common.s3.model.FileVisibility;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedPutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

@Service
public class DefaultS3PresignService implements S3PresignService {

    private static final int MIN_EXPIRE_SECONDS = 1;
    private static final Pattern USER_OWNED_PURPOSE_PATTERN =
            Pattern.compile("^([a-z0-9_-]+)-user-(\\d+)$");

    private final S3Presigner s3Presigner;
    private final S3Properties s3Properties;
    private final Clock clock;

    public DefaultS3PresignService(
            S3Presigner s3Presigner, S3Properties s3Properties, Clock clock) {
        this.s3Presigner = s3Presigner;
        this.s3Properties = s3Properties;
        this.clock = clock;
    }

    @Override
    public PresignedUrlResponse createUploadUrl(CreateUploadPresignedUrlRequest request) {
        requireNotBlank(request.purpose(), "purpose는 필수입니다.");
        requireNotBlank(request.fileName(), "fileName은 필수입니다.");
        requireNotBlank(request.contentType(), "contentType은 필수입니다.");
        validateSingleContentLength(request.contentLength());

        FileVisibility visibility = resolveVisibility(request.visibility());
        int expiresInSeconds = resolveExpiresInSeconds(request.expiresInSeconds());
        String key = buildObjectKey(visibility, request.purpose(), request.fileName());
        String cacheControl = resolveCacheControl(visibility);

        PutObjectRequest putObjectRequest =
                PutObjectRequest.builder()
                        .bucket(s3Properties.getBucket())
                        .key(key)
                        .contentType(request.contentType())
                        .cacheControl(cacheControl)
                        .build();

        PutObjectPresignRequest presignRequest =
                PutObjectPresignRequest.builder()
                        .signatureDuration(Duration.ofSeconds(expiresInSeconds))
                        .putObjectRequest(putObjectRequest)
                        .build();

        PresignedPutObjectRequest presignedRequest = s3Presigner.presignPutObject(presignRequest);

        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", request.contentType());
        headers.put("Cache-Control", cacheControl);

        return new PresignedUrlResponse(
                presignedRequest.url().toExternalForm(),
                "PUT",
                Map.copyOf(headers),
                key,
                Instant.now(clock).plusSeconds(expiresInSeconds));
    }

    @Override
    public List<PresignedUrlResponse> createUploadUrls(CreateUploadPresignedUrlsRequest request) {
        if (request == null || request.files() == null || request.files().isEmpty()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "files는 비어 있을 수 없습니다.");
        }

        int maxFileCount = s3Properties.getUploadLimit().getMaxFileCount();
        if (request.files().size() > maxFileCount) {
            throw new CommonException(
                    CommonErrorCode.INVALID_INPUT, "files 개수는 " + maxFileCount + " 이하여야 합니다.");
        }

        long maxTotalBytes = s3Properties.getUploadLimit().getMaxTotalBytes();
        long totalBytes = 0L;

        for (CreateUploadPresignedUrlRequest fileRequest : request.files()) {
            if (fileRequest == null) {
                throw new CommonException(
                        CommonErrorCode.INVALID_INPUT, "file 요청 값은 null일 수 없습니다.");
            }
            totalBytes =
                    safeAdd(totalBytes, validateSingleContentLength(fileRequest.contentLength()));
            if (totalBytes > maxTotalBytes) {
                throw new CommonException(
                        CommonErrorCode.INVALID_INPUT,
                        "전체 contentLength는 " + maxTotalBytes + " 바이트 이하여야 합니다.");
            }
        }

        List<PresignedUrlResponse> responses = new ArrayList<>(request.files().size());
        for (CreateUploadPresignedUrlRequest fileRequest : request.files()) {
            responses.add(createUploadUrl(fileRequest));
        }

        return List.copyOf(responses);
    }

    @Override
    public PresignedUrlResponse createDownloadUrl(CreateDownloadPresignedUrlRequest request) {
        requireNotBlank(request.key(), "key는 필수입니다.");

        FileVisibility visibility = resolveVisibility(request.visibility());
        if (visibility == FileVisibility.PUBLIC) {
            String objectUrl =
                    String.format(
                            Locale.ROOT,
                            "https://%s.s3.%s.amazonaws.com/%s",
                            s3Properties.getBucket(),
                            s3Properties.getRegion(),
                            request.key());
            return new PresignedUrlResponse(objectUrl, "GET", Map.of(), request.key(), null);
        }

        int expiresInSeconds = resolveExpiresInSeconds(request.expiresInSeconds());

        GetObjectRequest.Builder getObjectRequestBuilder =
                GetObjectRequest.builder()
                        .bucket(s3Properties.getBucket())
                        .key(request.key())
                        .responseCacheControl(s3Properties.getCache().getPrivateCacheControl());

        if (isNotBlank(request.downloadFileName())) {
            getObjectRequestBuilder.responseContentDisposition(
                    "attachment; filename=\""
                            + sanitizeFileName(request.downloadFileName())
                            + "\"");
        }

        GetObjectPresignRequest presignRequest =
                GetObjectPresignRequest.builder()
                        .signatureDuration(Duration.ofSeconds(expiresInSeconds))
                        .getObjectRequest(getObjectRequestBuilder.build())
                        .build();

        PresignedGetObjectRequest presignedRequest = s3Presigner.presignGetObject(presignRequest);

        return new PresignedUrlResponse(
                presignedRequest.url().toExternalForm(),
                "GET",
                Map.of(),
                request.key(),
                Instant.now(clock).plusSeconds(expiresInSeconds));
    }

    private int resolveExpiresInSeconds(Integer requestedExpiresInSeconds) {
        int expiresInSeconds =
                requestedExpiresInSeconds != null
                        ? requestedExpiresInSeconds
                        : s3Properties.getPresign().getDefaultExpireSeconds();

        if (expiresInSeconds < MIN_EXPIRE_SECONDS
                || expiresInSeconds > s3Properties.getPresign().getMaxExpireSeconds()) {
            throw new CommonException(
                    CommonErrorCode.INVALID_INPUT,
                    "expiresInSeconds는 "
                            + MIN_EXPIRE_SECONDS
                            + " 이상 "
                            + s3Properties.getPresign().getMaxExpireSeconds()
                            + " 이하여야 합니다.");
        }

        return expiresInSeconds;
    }

    private String resolveCacheControl(FileVisibility visibility) {
        return visibility == FileVisibility.PUBLIC
                ? s3Properties.getCache().getPublicCacheControl()
                : s3Properties.getCache().getPrivateCacheControl();
    }

    private long validateSingleContentLength(Long contentLength) {
        if (contentLength == null || contentLength <= 0) {
            throw new CommonException(
                    CommonErrorCode.INVALID_INPUT, "contentLength는 필수이며 0보다 커야 합니다.");
        }

        long maxSingleBytes = s3Properties.getUploadLimit().getMaxSingleBytes();
        if (contentLength > maxSingleBytes) {
            throw new CommonException(
                    CommonErrorCode.INVALID_INPUT,
                    "contentLength는 " + maxSingleBytes + " 바이트 이하여야 합니다.");
        }

        return contentLength;
    }

    private FileVisibility resolveVisibility(FileVisibility visibility) {
        return visibility != null ? visibility : FileVisibility.PRIVATE;
    }

    private static long safeAdd(long left, long right) {
        try {
            return Math.addExact(left, right);
        } catch (ArithmeticException ex) {
            throw new CommonException(
                    CommonErrorCode.INVALID_INPUT, "contentLength 합산 중 오버플로우가 발생했습니다.");
        }
    }

    private String buildObjectKey(FileVisibility visibility, String purpose, String fileName) {
        String visibilityPath = visibility.pathSegment();
        String uniqueId = UUID.randomUUID().toString().replace("-", "");
        String safeFileName = sanitizeFileName(fileName);
        String normalizedPurpose = purpose.trim().toLowerCase(Locale.ROOT);

        Matcher userOwnedMatcher = USER_OWNED_PURPOSE_PATTERN.matcher(normalizedPurpose);
        if (userOwnedMatcher.matches()) {
            String domainPurpose = sanitizePathSegment(userOwnedMatcher.group(1));
            String userId = userOwnedMatcher.group(2);

            return String.format(
                    Locale.ROOT,
                    "%s/%s/%s/%s_%s",
                    visibilityPath,
                    domainPurpose,
                    userId,
                    uniqueId,
                    safeFileName);
        }

        String safePurpose = sanitizePathSegment(normalizedPurpose);

        return String.format(
                Locale.ROOT, "%s/%s/%s_%s", visibilityPath, safePurpose, uniqueId, safeFileName);
    }

    private static void requireNotBlank(String value, String message) {
        if (!isNotBlank(value)) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, message);
        }
    }

    private static boolean isNotBlank(String value) {
        return value != null && !value.isBlank();
    }

    private static String sanitizePathSegment(String value) {
        String sanitized = value.trim().toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9_-]", "-");
        if (sanitized.isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "경로 세그먼트에 유효한 문자가 없습니다.");
        }
        return sanitized;
    }

    private static String sanitizeFileName(String value) {
        String normalized = value.trim().replace("\\", "_").replace("/", "_");
        String sanitized = normalized.replaceAll("[^a-zA-Z0-9._-]", "_");
        if (sanitized.isBlank()) {
            throw new CommonException(CommonErrorCode.INVALID_INPUT, "fileName에 유효한 문자가 없습니다.");
        }
        return sanitized;
    }
}
