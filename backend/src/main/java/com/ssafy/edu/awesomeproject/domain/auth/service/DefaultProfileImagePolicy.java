package com.ssafy.edu.awesomeproject.domain.auth.service;

import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import org.springframework.stereotype.Component;

@Component
public class DefaultProfileImagePolicy {
    private static final List<String> DEFAULT_PROFILE_IMAGE_KEYS =
            List.of(
                    "public/profile/default/profile_penguin.png",
                    "public/profile/default/profile_bear.png");

    public String pickRandomKey() {
        int index = ThreadLocalRandom.current().nextInt(DEFAULT_PROFILE_IMAGE_KEYS.size());
        return DEFAULT_PROFILE_IMAGE_KEYS.get(index);
    }
}
