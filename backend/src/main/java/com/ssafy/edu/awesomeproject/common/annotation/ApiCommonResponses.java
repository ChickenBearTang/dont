package com.ssafy.edu.awesomeproject.common.annotation;

import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@ApiResponses({
    @ApiResponse(responseCode = "400", description = "잘못된 요청"),
    @ApiResponse(responseCode = "401", description = "인증 필요"),
    @ApiResponse(responseCode = "403", description = "접근 권한 없음"),
    @ApiResponse(responseCode = "404", description = "리소스를 찾을 수 없음"),
    @ApiResponse(responseCode = "500", description = "서버 내부 오류")
})
public @interface ApiCommonResponses {}
