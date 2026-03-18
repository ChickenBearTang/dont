package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum AccountStatus {
    ACTIVE("활성"),
    INACTIVE("비활성"),
    CLOSED("해지"),
    SUSPENDED("정지");

    private final String description;
}
