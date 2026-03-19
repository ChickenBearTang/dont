package com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class OpenBankRequest {

    // global에서 만든 공통 헤더 객체를 사용
    @JsonProperty("Header")
    private OpenBankReqHeader header;

    // 만약 계좌 생성 API처럼 요청 바디(Body)에 추가 데이터가 필요하다면 작성
}
