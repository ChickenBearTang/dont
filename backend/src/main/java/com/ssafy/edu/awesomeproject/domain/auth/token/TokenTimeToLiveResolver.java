package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import org.springframework.stereotype.Component;

@Component
public class TokenTimeToLiveResolver {
    private final Clock clock;

    public TokenTimeToLiveResolver(Clock clock) {
        this.clock = clock;
    }

    public Duration resolve(Instant expiresAt) {
        Duration duration = Duration.between(Instant.now(clock), expiresAt);
        if (duration.isNegative()) {
            return Duration.ZERO;
        }

        return duration;
    }
}
