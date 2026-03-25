package com.ssafy.edu.awesomeproject.domain.community.service;

import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.community.dto.response.PrXaiAvailabilityResponseDto;
import com.ssafy.edu.awesomeproject.domain.community.entity.PrPost;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityErrorCode;
import com.ssafy.edu.awesomeproject.domain.community.error.CommunityException;
import com.ssafy.edu.awesomeproject.domain.community.repository.PrPostRepository;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import org.springframework.core.env.Environment;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PrXaiAvailabilityService {

    private static final String URL_MATCH_TYPE = "URL_EXACT";
    private static final String TITLE_PRICE_MATCH_TYPE = "TITLE_PRICE_SIMILAR";

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
            throw new CommunityException(
                    CommunityErrorCode.PURCHASE_REQUEST_XAI_UPSTREAM_ERROR, exception.getMessage());
        }

        return new PrXaiAvailabilityResponseDto(
                false, "No matching crawled item found yet.", null, null, null);
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

    private CrawlItemMatch findTitleAndPriceMatch(Connection connection, String itemName, long priceAmount)
            throws SQLException {
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

    private record CrawlItemMatch(String title, String url) {}
}
