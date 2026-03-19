package com.ssafy.edu.awesomeproject.common.s3.model;

import java.util.Locale;

public enum FileVisibility {
    PUBLIC,
    PRIVATE;

    public String pathSegment() {
        return name().toLowerCase(Locale.ROOT);
    }
}
