package com.ssafy.edu.awesomeproject.domain.auth.token;

import java.time.Duration;

public interface ReissueLockStore {
    boolean tryAcquireBySessionId(String sessionId, Duration timeToLive);

    void releaseBySessionId(String sessionId);
}
