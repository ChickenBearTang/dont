package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * Account 도메인 전용 규격화된 응답 DTO (Envelope Pattern)
 *
 * @param <T> 응답 데이터 타입
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PRIVATE)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
public class AccountApiResponse<T> {
    private boolean success;
    private String code;
    private String message;
    private T data;

    /** 성공 응답을 생성합니다. (기본 코드/메시지 사용) */
    public static <T> AccountApiResponse<T> success(T data) {
        return new AccountApiResponse<>(true, "200", "정상 처리되었습니다.", data);
    }

    /** 성공 응답을 생성합니다. (커스텀 코드/메시지 사용) */
    public static <T> AccountApiResponse<T> success(String code, String message, T data) {
        return new AccountApiResponse<>(true, code, message, data);
    }

    /** 실패 응답을 생성합니다. */
    public static <T> AccountApiResponse<T> error(String code, String message) {
        return new AccountApiResponse<>(false, code, message, null);
    }
}
