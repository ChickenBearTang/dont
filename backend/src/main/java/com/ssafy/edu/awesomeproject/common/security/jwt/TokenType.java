package com.ssafy.edu.awesomeproject.common.security.jwt;

public enum TokenType {
    ACCESS("access"),
    REFRESH("refresh");

    private final String value;

    TokenType(String value) {
        this.value = value;
    }

    public String value() {
        return value;
    }

    public static TokenType fromValue(String value) {
        for (TokenType tokenType : values()) {
            if (tokenType.value.equals(value)) {
                return tokenType;
            }
        }

        throw new IllegalArgumentException("Unknown token type: " + value);
    }
}
