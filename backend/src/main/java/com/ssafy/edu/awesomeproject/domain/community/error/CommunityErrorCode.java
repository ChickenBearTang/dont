package com.ssafy.edu.awesomeproject.domain.community.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum CommunityErrorCode implements ErrorCode {
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "COMM_400_1", "잘못된 입력입니다."),
    BOARD_NOT_FOUND(HttpStatus.BAD_REQUEST, "COMM_400_2", "유효한 게시판이 아닙니다."),
    COHORT_ID_REQUIRED(HttpStatus.BAD_REQUEST, "COMM_400_3", "기수 게시판은 generationNo 필요합니다."),
    INVALID_CATEGORY_AND_COHORT(
            HttpStatus.BAD_REQUEST, "COMM_400_4", "기수 게시판이 아닌 경우 generationNo 사용할 수 없습니다."),
    COHORT_NOT_FOUND(HttpStatus.BAD_REQUEST, "COMM_400_5", "존재하지 않는 기수입니다."),

    POST_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_1", "게시글을 찾을 수 없습니다."),
    COMMENT_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_2", "댓글을 찾을 수 없습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_3", "사용자를 찾을 수 없습니다."),

    POST_FORBIDDEN(HttpStatus.FORBIDDEN, "COMM_403_1", "해당 글에 대한 권한이 없습니다."),
    COHORT_FORBIDDEN(HttpStatus.FORBIDDEN, "COMM_403_2", "해당 기수 게시판에 대한 권한이 없습니다."),
    COMMENT_FORBIDDEN(HttpStatus.FORBIDDEN, "COMM_403_3", "해당 댓글에 대한 권한이 없습니다."),

    INVALID_PARENT_COMMENT(HttpStatus.BAD_REQUEST, "COMM_400_6", "유효하지 않은 부모 댓글입니다.");

    private HttpStatus httpStatus;
    private String code;
    private String message;

    CommunityErrorCode(HttpStatus httpStatus, String code, String message) {
        this.httpStatus = httpStatus;
        this.code = code;
        this.message = message;
    }

    @Override
    public HttpStatus status() {
        return httpStatus;
    }

    @Override
    public String code() {
        return code;
    }

    @Override
    public String message() {
        return message;
    }
}
