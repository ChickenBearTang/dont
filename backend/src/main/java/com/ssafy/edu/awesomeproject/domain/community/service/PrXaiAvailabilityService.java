package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Locale;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PrXaiAvailabilityService {

    private static final String URL_MATCH_TYPE = "URL_EXACT";
    private static final String TITLE_PRICE_MATCH_TYPE = "TITLE_PRICE_SIMILAR";
    private static final String FALLBACK_NO_MATCH_TYPE = "NO_MATCH_FALLBACK";
    private static final String FALLBACK_CHECK_SKIPPED_TYPE = "CHECK_SKIPPED";
    private static final String ITEM_WHITELIST_ONLY_TYPE = "ITEM_WHITELIST_ONLY";
    private static final List<String> SUPPORTED_ITEM_NAMES =
            List.of("F87", "VXE R1", "MX Master 3S");
    private static final List<String> SUPPORTED_ITEM_TOKENS =
            List.of("f87", "f87pro", "vxer1", "mxmaster3", "mxmaster3s");

    private final PrPostRepository prPostRepository;
    private final UserRepository userRepository;
    private final Environment environment;

    public PrXaiAvailabilityService(
            PrPostRepository prPostRepository,
            UserRepository userRepository,
            Environment environment) {
        this.prPostRepository = prPostRepository;
        this.userRepository = userRepository;
        this.environment = environment;
    }

    @Transactional(readOnly = true)
    public PrXaiAvailabilityResponseDto checkAvailability(Long postId, Long userId) {
        if (userId == null) {
            throw new CommunityException(CommunityErrorCode.PURCHASE_REQUEST_FORBIDDEN);
        }
        userRepository
                .findActiveById(userId)
                .orElseThrow(() -> new CommunityException(CommunityErrorCode.USER_NOT_FOUND));

        PrPost prPost =
                prPostRepository
                        .findByPost_Id(postId)
                        .orElseThrow(
                                () ->
                                        new CommunityException(
                                                CommunityErrorCode.PURCHASE_REQUEST_NOT_FOUND));

        String purchaseUrl = blankToNull(prPost.getPurchaseUrl());
        String itemName = blankToNull(prPost.getItemName());
        long priceAmount = prPost.getPriceAmount() == null ? 0L : prPost.getPriceAmount();

        if (itemName == null && purchaseUrl == null) {
            return new PrXaiAvailabilityResponseDto(
                    false, "No purchase URL or item name.", null, null, null);
        }

        if (!isWhitelistedItem(itemName, purchaseUrl)) {
            return new PrXaiAvailabilityResponseDto(
                    false,
                    "XAI item support is limited to %s."
                            .formatted(String.join(", ", SUPPORTED_ITEM_NAMES)),
                    ITEM_WHITELIST_ONLY_TYPE,
                    null,
                    null);
        }

        try (Connection connection = createConnection()) {
            CrawlItemMatch urlMatch = findUrlExactMatch(connection, purchaseUrl);
            if (urlMatch != null) {
                return new PrXaiAvailabilityResponseDto(
                        true,
                        "Matched with crawled item URL.",
                        URL_MATCH_TYPE,
                        urlMatch.title(),
                        urlMatch.url());
            }

            CrawlItemMatch titleMatch = findTitleAndPriceMatch(connection, itemName, priceAmount);
            if (titleMatch != null) {
                return new PrXaiAvailabilityResponseDto(
                        true,
                        "Matched with crawled item title and price range.",
                        TITLE_PRICE_MATCH_TYPE,
                        titleMatch.title(),
                        titleMatch.url());
            }
        } catch (SQLException exception) {
            return new PrXaiAvailabilityResponseDto(
                    true,
                    "Crawl matching check failed. XAI evaluation will proceed with PR request context.",
                    FALLBACK_CHECK_SKIPPED_TYPE,
                    null,
                    purchaseUrl);
        }

        return new PrXaiAvailabilityResponseDto(
                true,
                "No matching crawled item found. XAI evaluation will proceed with PR request context.",
                FALLBACK_NO_MATCH_TYPE,
                null,
                purchaseUrl);
    }

    private Connection createConnection() throws SQLException {
        String host = getProperty("AI_POSTGRES_HOST", "ai.postgres.host", "127.0.0.1");
        String port = getProperty("AI_POSTGRES_PORT", "ai.postgres.port", "55432");
        String db = getProperty("AI_POSTGRES_DB", "ai.postgres.db", "ai_crawl");
        String user = getProperty("AI_POSTGRES_USER", "ai.postgres.user", "ai_user");
        String password =
                getProperty("AI_POSTGRES_PASSWORD", "ai.postgres.password", "ai_password");

        String jdbcUrl = "jdbc:postgresql://%s:%s/%s".formatted(host, port, db);
        return DriverManager.getConnection(jdbcUrl, user, password);
    }

    private String getProperty(String key, String relaxedKey, String defaultValue) {
        String direct = blankToNull(environment.getProperty(key));
        if (direct != null) {
            return direct;
        }
        String relaxed = blankToNull(environment.getProperty(relaxedKey));
        return relaxed == null ? defaultValue : relaxed;
    }

    private CrawlItemMatch findUrlExactMatch(Connection connection, String purchaseUrl)
            throws SQLException {
        if (purchaseUrl == null) {
            return null;
        }
        String sql =
                """
                SELECT title, url
                FROM crawl_items
                WHERE COALESCE(is_outlier, FALSE) = FALSE
                  AND url = ?
                ORDER BY last_seen_at DESC
                LIMIT 1
                """;
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, purchaseUrl);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (!resultSet.next()) {
                    return null;
                }
                return new CrawlItemMatch(resultSet.getString("title"), resultSet.getString("url"));
            }
        }
    }

    private CrawlItemMatch findTitleAndPriceMatch(
            Connection connection, String itemName, long priceAmount) throws SQLException {
        if (itemName == null) {
            return null;
        }

        long tolerance = Math.max((long) (priceAmount * 0.2), 50_000L);
        long lowerBound = Math.max(priceAmount - tolerance, 0L);
        long upperBound = priceAmount + tolerance;

        String sql =
                """
                SELECT title, url
                FROM crawl_items
                WHERE COALESCE(is_outlier, FALSE) = FALSE
                  AND LOWER(title) LIKE LOWER(?)
                  AND (
                        ? <= 0
                        OR NULLIF(regexp_replace(COALESCE(price, ''), '[^0-9]', '', 'g'), '')::BIGINT
                           BETWEEN ? AND ?
                      )
                ORDER BY last_seen_at DESC
                LIMIT 1
                """;

        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, "%" + itemName + "%");
            statement.setLong(2, priceAmount);
            statement.setLong(3, lowerBound);
            statement.setLong(4, upperBound);
            try (ResultSet resultSet = statement.executeQuery()) {
                if (!resultSet.next()) {
                    return null;
                }
                return new CrawlItemMatch(resultSet.getString("title"), resultSet.getString("url"));
            }
        }
    }

    private String blankToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private boolean isWhitelistedItem(String itemName, String purchaseUrl) {
        String decodedPurchaseUrl = decodeUrlSafe(safe(purchaseUrl));
        String normalizedContext =
                normalizeForItemMatch("%s %s".formatted(safe(itemName), decodedPurchaseUrl));
        if (normalizedContext.isEmpty()) {
            return false;
        }
        if (SUPPORTED_ITEM_TOKENS.stream().anyMatch(normalizedContext::contains)) {
            return true;
        }
        if (isF87Alias(normalizedContext)) {
            return true;
        }
        return isMxMasterAlias(normalizedContext);
    }

    private boolean isF87Alias(String normalizedContext) {
        if (normalizedContext.isEmpty()) {
            return false;
        }
        boolean hasF87Keyword =
                normalizedContext.contains("f87")
                        || normalizedContext.contains("f87pro")
                        || normalizedContext.contains("\uB3C5\uAC70\uBBF887");
        boolean hasSpider87 =
                normalizedContext.contains("\uB3C5\uAC70\uBBF8") && normalizedContext.contains("87");
        return hasF87Keyword || hasSpider87;
    }

    private boolean isMxMasterAlias(String normalizedContext) {
        if (normalizedContext.isEmpty()) {
            return false;
        }
        boolean hasMxToken = normalizedContext.contains("mx");
        boolean hasMasterLikeToken =
                normalizedContext.contains("master")
                        || normalizedContext.contains("\uB9C8\uC2A4\uD130")
                        || normalizedContext.contains("\uB9C8\uC6B0\uC2A4")
                        || normalizedContext.contains("\uB9C8\uC2A4\uC5B4");
        boolean hasModelToken = normalizedContext.contains("3s") || normalizedContext.contains("3");
        return hasMxToken && hasMasterLikeToken && hasModelToken;
    }

    private String decodeUrlSafe(String value) {
        if (value.isBlank()) {
            return value;
        }
        try {
            return URLDecoder.decode(value, StandardCharsets.UTF_8);
        } catch (IllegalArgumentException exception) {
            return value;
        }
    }

    private String normalizeForItemMatch(String value) {
        return value.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9\\uac00-\\ud7a3]", "");
    }

    private String safe(String value) {
        return value == null ? "" : value;
    }

    private record CrawlItemMatch(String title, String url) {}
}
