package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;


@Getter
@NoArgsConstructor(access = AccessLevel.PRIVATE)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class AccountApiResponse<T> {
    private boolean success;
    private String code;
    private String message;
    private T data;


    public static <T> AccountApiResponse<T> success(T data) {
        return new AccountApiResponse<>(true, "200", "정상 처리되었습니다.", data);
    }


    public static <T> AccountApiResponse<T> success(String code, String message, T data) {
        return new AccountApiResponse<>(true, code, message, data);
    }


    public static <T> AccountApiResponse<T> error(String code, String message) {
        return new AccountApiResponse<>(false, code, message, null);
    }
}
