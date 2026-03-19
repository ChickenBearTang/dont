package com.ssafy.edu.awesomeproject.common.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.validation.annotation.Validated;

@Component
@Validated
@ConfigurationProperties(prefix = "aws.s3")
public class S3Properties {

    @NotBlank private String bucket;

    @NotBlank private String region;

    @Valid private PresignProperties presign = new PresignProperties();

    @Valid private UploadLimitProperties uploadLimit = new UploadLimitProperties();

    @Valid private CacheProperties cache = new CacheProperties();

    public String getBucket() {
        return bucket;
    }

    public void setBucket(String bucket) {
        this.bucket = bucket;
    }

    public String getRegion() {
        return region;
    }

    public void setRegion(String region) {
        this.region = region;
    }

    public PresignProperties getPresign() {
        return presign;
    }

    public void setPresign(PresignProperties presign) {
        this.presign = presign;
    }

    public UploadLimitProperties getUploadLimit() {
        return uploadLimit;
    }

    public void setUploadLimit(UploadLimitProperties uploadLimit) {
        this.uploadLimit = uploadLimit;
    }

    public CacheProperties getCache() {
        return cache;
    }

    public void setCache(CacheProperties cache) {
        this.cache = cache;
    }

    public static class PresignProperties {

        @Min(1)
        @Max(3600)
        private int defaultExpireSeconds = 300;

        @Min(1)
        @Max(3600)
        private int maxExpireSeconds = 900;

        public int getDefaultExpireSeconds() {
            return defaultExpireSeconds;
        }

        public void setDefaultExpireSeconds(int defaultExpireSeconds) {
            this.defaultExpireSeconds = defaultExpireSeconds;
        }

        public int getMaxExpireSeconds() {
            return maxExpireSeconds;
        }

        public void setMaxExpireSeconds(int maxExpireSeconds) {
            this.maxExpireSeconds = maxExpireSeconds;
        }
    }

    public static class UploadLimitProperties {

        @Min(1)
        private long maxSingleBytes = 10L * 1024 * 1024;

        @Min(1)
        private long maxTotalBytes = 50L * 1024 * 1024;

        @Min(1)
        @Max(100)
        private int maxFileCount = 10;

        public long getMaxSingleBytes() {
            return maxSingleBytes;
        }

        public void setMaxSingleBytes(long maxSingleBytes) {
            this.maxSingleBytes = maxSingleBytes;
        }

        public long getMaxTotalBytes() {
            return maxTotalBytes;
        }

        public void setMaxTotalBytes(long maxTotalBytes) {
            this.maxTotalBytes = maxTotalBytes;
        }

        public int getMaxFileCount() {
            return maxFileCount;
        }

        public void setMaxFileCount(int maxFileCount) {
            this.maxFileCount = maxFileCount;
        }
    }

    public static class CacheProperties {

        @NotBlank private String publicCacheControl = "public, max-age=31536000, immutable";

        @NotBlank private String privateCacheControl = "private, no-store";

        public String getPublicCacheControl() {
            return publicCacheControl;
        }

        public void setPublicCacheControl(String publicCacheControl) {
            this.publicCacheControl = publicCacheControl;
        }

        public String getPrivateCacheControl() {
            return privateCacheControl;
        }

        public void setPrivateCacheControl(String privateCacheControl) {
            this.privateCacheControl = privateCacheControl;
        }
    }
}
