package com.ssafy.edu.awesomeproject.sample.presentation;

import com.ssafy.edu.awesomeproject.common.error.CommonErrorCode;
import com.ssafy.edu.awesomeproject.common.error.CommonException;
import com.ssafy.edu.awesomeproject.common.response.CommonResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/examples")
public class ExampleController {

    @GetMapping("/ping")
    public CommonResponse<Map<String, String>> ping() {
        return CommonResponse.success(Map.of("message", "pong"));
    }

    @PostMapping("/echo")
    public CommonResponse<Map<String, String>> echo(@Valid @RequestBody EchoRequest request) {
        return CommonResponse.success(Map.of("message", request.message().trim()));
    }

    @GetMapping("/rules/{number}")
    public CommonResponse<Map<String, Integer>> rules(@PathVariable int number) {
        if ((number & 1) == 1) {
            throw new CommonException(
                    CommonErrorCode.BUSINESS_RULE_VIOLATION, Map.of("number", number));
        }

        return CommonResponse.success(Map.of("number", number));
    }

    public record EchoRequest(@NotBlank String message) {}
}
