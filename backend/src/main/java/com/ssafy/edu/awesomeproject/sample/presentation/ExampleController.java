package com.ssafy.edu.awesomeproject.sample.presentation;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Positive;
import java.time.Clock;
import java.time.OffsetDateTime;
import java.util.Map;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/examples")
@Tag(name = "Example", description = "예제/헬스체크 API")
public class ExampleController {

    private final Clock clock;

    public ExampleController(Clock clock) {
        this.clock = clock;
    }

    @GetMapping("/ping")
    @Operation(
            summary = "서버 상태 확인",
            description = "서버 응답 + 현재 시각 반환",
            security = {})
    @ApiResponses({
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "200",
                description = "정상 응답"),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "500",
                description = "서버 내부 오류",
                content = @Content(schema = @Schema(implementation = ApiResponse.class)))
    })
    public ApiResponse<Map<String, Object>> ping() {
        return ApiResponse.success(
                Map.of("message", "pong", "serverTime", OffsetDateTime.now(clock)));
    }

    @PostMapping("/echo")
    @Operation(
            summary = "메시지 에코",
            description = "입력 메시지를 그대로 반환하며 길이 정보 포함",
            security = {})
    @ApiResponses({
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "200",
                description = "정상 응답"),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "400",
                description = "요청 값 검증 실패",
                content = @Content(schema = @Schema(implementation = ApiResponse.class))),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "500",
                description = "서버 내부 오류",
                content = @Content(schema = @Schema(implementation = ApiResponse.class)))
    })
    public ApiResponse<Map<String, String>> echo(@Valid @RequestBody EchoRequest request) {
        return ApiResponse.success(
                Map.of(
                        "message", request.message().trim(),
                        "length", String.valueOf(request.message().trim().length())));
    }

    @GetMapping("/rules/{number}")
    @Operation(
            summary = "짝수 규칙 검증",
            description = "짝수만 허용. 홀수 입력 시 비즈니스 규칙 위반 에러",
            security = {})
    @ApiResponses({
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "200",
                description = "정상 응답"),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "400",
                description = "요청 값 검증 실패",
                content = @Content(schema = @Schema(implementation = ApiResponse.class))),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "409",
                description = "비즈니스 규칙 위반",
                content = @Content(schema = @Schema(implementation = ApiResponse.class))),
        @io.swagger.v3.oas.annotations.responses.ApiResponse(
                responseCode = "500",
                description = "서버 내부 오류",
                content = @Content(schema = @Schema(implementation = ApiResponse.class)))
    })
    public ApiResponse<Map<String, Integer>> rules(@PathVariable @Positive int number) {
        if (number % 2 != 0) {
            throw new CommonException(
                    CommonErrorCode.BUSINESS_RULE_VIOLATION, Map.of("number", number));
        }
        return ApiResponse.success(Map.of("acceptedNumber", number));
    }
}
