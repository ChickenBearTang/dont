package com.ssafy.edu.awesomeproject.domain.auth.token;

public record StoredRefreshToken(String tokenHash, String tokenId, Long userId) {}
