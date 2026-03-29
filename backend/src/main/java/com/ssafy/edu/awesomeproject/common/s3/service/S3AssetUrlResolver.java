package com.ssafy.edu.awesomeproject.common.s3.service;

import org.springframework.stereotype.Component;

@Component
public class S3AssetUrlResolver {
    private static final String PUBLIC_KEY_PREFIX = "public/";
    private static final String PRIVATE_KEY_PREFIX = "private/";

    private final S3FileTemplateService s3FileTemplateService;

    public S3AssetUrlResolver(S3FileTemplateService s3FileTemplateService) {
        this.s3FileTemplateService = s3FileTemplateService;
    }

    public String resolvePublicUrlOrNull(String key) {
        if (key == null || key.isBlank()) {
            return null;
        }

        if (!isPublicKey(key)) {
            return key;
        }

        return s3FileTemplateService.buildPublicObjectUrl(key);
    }

    public boolean isPublicKey(String key) {
        return key != null && key.startsWith(PUBLIC_KEY_PREFIX);
    }

    public boolean isPrivateKey(String key) {
        return key != null && key.startsWith(PRIVATE_KEY_PREFIX);
    }
}
