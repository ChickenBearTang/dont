package com.ssafy.edu.awesomeproject.domain.fin.account.entity;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum AccountRole {
    LINKED_DEPOSIT("연결계좌"),
    SAVE_BOX("세이브박스");

    private final String description;
}
