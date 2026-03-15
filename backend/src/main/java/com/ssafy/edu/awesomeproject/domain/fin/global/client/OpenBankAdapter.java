package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Random;

@Component
@RequiredArgsConstructor
public class OpenBankAdapter {

    private final OpenBankClient openBankClient;

    @Value("${auth.api.key}")
    private String apiKey;

    public AccountListResponse fetchDemandDepositAccounts(String userKey) {
        // 1. 외부 API용 요청 객체(Request) 생성
        OpenBankRequest request = createAccountListRequest(userKey);

        // 2. 외부 API 호출
        OpenBankResponse response = openBankClient.fetchDemandDepositAccounts(request);

        // 3. 외부 API 응답을 우리 서버용 DTO로 변환 (Mapping)
        return AccountListResponse.from(response);
    }

    private OpenBankRequest createAccountListRequest(String userKey) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankRequest.builder()
            .header(OpenBankReqHeader.builder()
                .apiName("inquireDemandDepositAccountList")
                .transmissionDate(now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                .institutionCode("00100")
                .fintechAppNo("001")
                .apiServiceCode("inquireDemandDepositAccountList")
                .institutionTransactionUniqueNo(generateUniqueNo(now))
                .apiKey(apiKey)
                .userKey(userKey)
                .build())
            .build();
    }

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = new Random().nextInt(900000) + 100000; // 6자리 랜덤수
        return timestamp + randomNo;
    }
}