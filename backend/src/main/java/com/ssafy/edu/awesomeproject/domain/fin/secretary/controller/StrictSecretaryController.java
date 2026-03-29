package com.ssafy.edu.awesomeproject.domain.fin.secretary.controller;

import com.ssafy.edu.awesomeproject.common.annotation.CurrentUserId;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.AiClient;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.request.TtsRequest;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response.StrictSecretaryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.secretary.service.StrictSecretaryService;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("fin/strict-secretary")
public class StrictSecretaryController {

    private final StrictSecretaryService strictSecretaryService;
    private final AiClient aiClient;

    @PostMapping("/evaluate")
    @Operation(summary = "구매 요청 판단", description = "아이템 구매 요청에 대해 AI가 엄격하게 조언합니다.")
    public ResponseEntity<StrictSecretaryResponse> evaluatePurchase(
            @CurrentUserId Long userId, @RequestBody StrictSecretaryRequestDto requestBody) {

        StrictSecretaryResponse response =
                strictSecretaryService.evaluatePurchase(
                        userId,
                        requestBody.getItem_text(),
                        requestBody.getItem_link(),
                        requestBody.getUser_reason());

        log.info(
                "strict-secretary controller response. userId={}, approved={}, reasoningCount={}, commentLength={}",
                userId,
                response.isApproved(),
                response.getReasoning() == null ? 0 : response.getReasoning().size(),
                response.getFactViolenceComment() == null
                        ? 0
                        : response.getFactViolenceComment().length());
        return ResponseEntity.ok(response);
    }

    @PostMapping(value = "/tts", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    @Operation(summary = "독설 코멘트 TTS 생성", description = "텍스트를 오디오 파일로 변환해 반환합니다.")
    public ResponseEntity<byte[]> getTtsAudio(@RequestBody TtsRequest request) {
        byte[] audio = aiClient.getTtsAudio(request);
        return ResponseEntity.ok(audio);
    }

    @lombok.Getter
    @lombok.Setter
    public static class StrictSecretaryRequestDto {
        private String item_text;
        private String item_link;
        private String user_reason;
    }
}
