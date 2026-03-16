package com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.request;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.Builder;

/** 외부 은행 API의 '계좌 상세 조회' 요청을 위한 DTO */
@Builder
public record OpenBankDetailAccountRequest(OpenBankReqHeader header, String accountNo) {}
