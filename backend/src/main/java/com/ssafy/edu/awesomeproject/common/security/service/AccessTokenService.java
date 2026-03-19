package com.ssafy.edu.awesomeproject.common.security.service;

import com.ssafy.edu.awesomeproject.common.security.error.TokenErrorCode;
import com.ssafy.edu.awesomeproject.common.security.error.TokenException;
import com.ssafy.edu.awesomeproject.common.security.jwt.IssuedToken;
import com.ssafy.edu.awesomeproject.common.security.jwt.JwtTokenSpec;
import com.ssafy.edu.awesomeproject.common.security.jwt.ParsedToken;
import com.ssafy.edu.awesomeproject.common.security.jwt.TokenType;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.RequiredTypeException;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Service
public class AccessTokenService {
    private final SecretKey secretKey;
    private final String issuer;

    public AccessTokenService(
            @Value("${auth.jwt.secret}") String secret,
            @Value("${auth.jwt.issuer}") String issuer) {
        byte[] secretBytes = secret.getBytes(StandardCharsets.UTF_8);

        this.secretKey = Keys.hmacShaKeyFor(secretBytes);
        this.issuer = issuer;
    }

    public IssuedToken issue(JwtTokenSpec jwtTokenSpec) {
        Instant now = Instant.now();
        Instant expiresAt = now.plusSeconds(jwtTokenSpec.ttlSeconds());
        Map<String, Object> claims = new HashMap<>(jwtTokenSpec.claims());

        claims.put("typ", jwtTokenSpec.tokenType().value());
        if (jwtTokenSpec.sessionId() != null) {
            claims.put("sid", jwtTokenSpec.sessionId());
        }

        String accessToken =
                Jwts.builder()
                        .issuer(issuer)
                        .subject(jwtTokenSpec.subject())
                        .id(jwtTokenSpec.tokenId())
                        .claims(claims)
                        .issuedAt(Date.from(now))
                        .expiration(Date.from(expiresAt))
                        .signWith(secretKey)
                        .compact();

        return new IssuedToken(accessToken, "Bearer", jwtTokenSpec.ttlSeconds());
    }

    public ParsedToken parseAccessToken(String token) {
        try {
            return parse(token, TokenType.ACCESS);
        } catch (TokenException exception) {
            if (exception.getErrorCode() == TokenErrorCode.TOKEN_EXPIRED) {
                throw new TokenException(TokenErrorCode.ACCESS_TOKEN_EXPIRED);
            }

            throw exception;
        }
    }

    public ParsedToken parseRefreshToken(String token) {
        ParsedToken parsedToken;
        try {
            parsedToken = parse(token, TokenType.REFRESH);
        } catch (TokenException exception) {
            if (exception.getErrorCode() == TokenErrorCode.TOKEN_EXPIRED) {
                throw new TokenException(TokenErrorCode.REFRESH_TOKEN_EXPIRED);
            }

            throw exception;
        }

        if (parsedToken.sessionId() == null || parsedToken.sessionId().isBlank()) {
            throw new TokenException(TokenErrorCode.TOKEN_SESSION_INVALID);
        }

        return parsedToken;
    }

    private ParsedToken parse(String token, TokenType expectedType) {
        Claims claims = parseClaims(token);
        TokenType actualType = parseTokenType(claims);

        if (actualType != expectedType) {
            throw new TokenException(
                    TokenErrorCode.TOKEN_TYPE_MISMATCH,
                    Map.of("expected", expectedType.value(), "actual", actualType.value()));
        }

        return new ParsedToken(
                claims.getSubject(),
                claims.getId(),
                actualType,
                getOptionalStringClaim(claims, "sid"),
                getExpiration(claims),
                new HashMap<>(claims));
    }

    private Claims parseClaims(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(secretKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (ExpiredJwtException exception) {
            throw new TokenException(TokenErrorCode.TOKEN_EXPIRED);
        } catch (JwtException | IllegalArgumentException exception) {
            if (exception.getClass().getSimpleName().contains("Signature")) {
                throw new TokenException(TokenErrorCode.INVALID_TOKEN_SIGNATURE);
            }

            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
    }

    private TokenType parseTokenType(Claims claims) {
        try {
            return TokenType.fromValue(claims.get("typ", String.class));
        } catch (IllegalArgumentException
                | NullPointerException
                | RequiredTypeException exception) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
    }

    private String getOptionalStringClaim(Claims claims, String claimName) {
        try {
            return claims.get(claimName, String.class);
        } catch (RequiredTypeException exception) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }
    }

    private Instant getExpiration(Claims claims) {
        Date expiration = claims.getExpiration();
        if (expiration == null) {
            throw new TokenException(TokenErrorCode.TOKEN_INVALID);
        }

        return expiration.toInstant();
    }
}
