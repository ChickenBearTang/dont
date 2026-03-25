package com.ssafy.edu.awesomeproject.domain.community.error;

import com.ssafy.edu.awesomeproject.common.error.ErrorCode;
import org.springframework.http.HttpStatus;

public enum CommunityErrorCode implements ErrorCode {
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "COMM_400_1", "잘못된 입력입니다."),
    BOARD_NOT_FOUND(HttpStatus.BAD_REQUEST, "COMM_400_2", "유효한 게시판이 아닙니다."),
    COHORT_ID_REQUIRED(
            HttpStatus.BAD_REQUEST, "COMM_400_3", "기수 게시판은 generationNo가 필요합니다."),
    INVALID_CATEGORY_AND_COHORT(
            HttpStatus.BAD_REQUEST,
            "COMM_400_4",
            "기수 게시판이 아닌 경우 generationNo를 사용할 수 없습니다."),
    COHORT_NOT_FOUND(HttpStatus.BAD_REQUEST, "COMM_400_5", "존재하지 않는 기수입니다."),
    INVALID_PARENT_COMMENT(HttpStatus.BAD_REQUEST, "COMM_400_6", "유효하지 않은 부모 댓글입니다."),
    COMMENT_DEPTH_LIMIT_EXCEEDED(
            HttpStatus.BAD_REQUEST, "COMM_400_7", "대댓글은 최대 5단계까지만 작성할 수 있습니다."),

    POST_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_1", "게시글을 찾을 수 없습니다."),
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_2", "사용자를 찾을 수 없습니다."),
    COMMENT_NOT_FOUND(HttpStatus.NOT_FOUND, "COMM_404_3", "댓글을 찾을 수 없습니다."),

    POST_FORBIDDEN(HttpStatus.FORBIDDEN, "COMM_403_1", "해당 글에 대한 권한이 없습니다."),
    COHORT_FORBIDDEN(
            HttpStatus.FORBIDDEN, "COMM_403_2", "해당 기수 게시판에 대한 권한이 없습니다."),
    COMMENT_FORBIDDEN(HttpStatus.FORBIDDEN, "COMM_403_3", "해당 댓글에 대한 권한이 없습니다."),

    ALREADY_REACTED(HttpStatus.CONFLICT, "COMM_409_1", "이미 반응을 등록했습니다."),

    POLL_NOT_FOUND(HttpStatus.NOT_FOUND, "POLL_404_1", "투표 게시글을 찾을 수 없습니다."),
    POLL_NOT_OPEN(HttpStatus.CONFLICT, "POLL_409_1", "종료된 투표에는 참여할 수 없습니다."),

    HOTDEAL_NOT_FOUND(HttpStatus.NOT_FOUND, "HD_404_1", "핫딜을 찾을 수 없습니다."),

    PURCHASE_REQUEST_FORBIDDEN(HttpStatus.FORBIDDEN, "PR_403_1", "해당 PR에 대한 권한이 없습니다."),
    PURCHASE_REQUEST_NOT_FOUND(HttpStatus.NOT_FOUND, "PR_404_1", "PR을 찾을 수 없습니다."),
    PURCHASE_REQUEST_ALREADY_EXISTS(HttpStatus.CONFLICT, "PR_409_1", "해당 게시글에는 PR이 이미 존재합니다."),
    PURCHASE_REQUEST_NOT_OPEN(HttpStatus.CONFLICT, "PR_409_2", "열려있는 PR에서만 투표할 수 있습니다."),
    PURCHASE_REQUEST_XAI_UPSTREAM_ERROR(HttpStatus.BAD_GATEWAY, "PR_502_1", "XAI 평가 서버 호출에 실패했습니다."),
    PURCHASE_REQUEST_XAI_TIMEOUT(HttpStatus.GATEWAY_TIMEOUT, "PR_504_1", "XAI 평가 응답 시간이 초과되었습니다."),

    REPORT_TARGET_NOT_FOUND(HttpStatus.NOT_FOUND, "REPORT_404_1", "신고 대상을 찾을 수 없습니다."),
    REPORT_NOT_FOUND(HttpStatus.NOT_FOUND, "REPORT_404_2", "신고를 찾을 수 없습니다."),
    REPORT_ALREADY_EXISTS(HttpStatus.CONFLICT, "REPORT_409_1", "이미 신고한 대상입니다."),
    REPORT_ALREADY_PROCESSED(HttpStatus.CONFLICT, "REPORT_409_2", "이미 처리된 신고입니다."),
    SELF_REPORT_NOT_ALLOWED(
            HttpStatus.BAD_REQUEST, "REPORT_400_1", "본인이 작성한 대상은 신고할 수 없습니다.");

    private final HttpStatus httpStatus;
    private final String code;
    private final String message;

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
