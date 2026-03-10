package com.ssafy.edu.awesomeproject.common.security.jwt;

public record IssuedToken(String accessToken, String tokenType, long expiresInSeconds) {}
