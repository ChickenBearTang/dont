package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankClient;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader; // 🌟 추가된 공통 헤더 import
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Random;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class FinService {

    private final OpenBankClient openBankClient;

    @Value("${auth.api.key}")
    private String apiKey;

    public AccountListResponse getAccountList(Long userId) {
        // 1. 유저 키 조회 (임시. 차후 수정해서 DB에서 해당 userId의 userKey를 가져와야 함)
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767";

        // 2. 외부 API용 요청 객체(Request) 생성
        OpenBankRequest request = createAccountListRequest(userKey);

        // 3. 외부 API 호출
        OpenBankResponse response = openBankClient.fetchDemandDepositAccounts(request);

        // 4. 외부 API 응답을 우리 서버용 DTO로 변환 (Mapping)
        return convertToAccountListResponse(response);
    }

    /**
     * 외부 API 규격에 맞는 요청 헤더와 바디를 생성합니다.
     */
    private OpenBankRequest createAccountListRequest(String userKey) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankRequest.builder()
            // 🌟 변경된 부분: 내부 클래스 대신 공통(global) 헤더 빌더를 사용합니다.
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

    /**
     * 외부 API의 응답 데이터를 우리 서비스에 필요한 형태(DTO)로 가공합니다.
     */
    private AccountListResponse convertToAccountListResponse(OpenBankResponse response) {
        // REC 목록이 비어있을 경우를 대비해 null 체크 후 변환
        if (response.getRec() == null) {
            return AccountListResponse.builder().build();
        }

        return AccountListResponse.builder()
            .accounts(response.getRec().stream()
                .map(rec -> AccountListResponse.AccountDetail.builder()
                    .bankName(rec.getBankName())
                    .accountNo(rec.getAccountNo())
                    .accountName(rec.getAccountName())
                    .build())
                .collect(Collectors.toList()))
            .build();
    }

    /**
     * 20자리의 고유 거래 번호를 생성합니다. (날짜시간 + 랜덤숫자)
     */
    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = new Random().nextInt(900000) + 100000; // 6자리 랜덤수
        return timestamp + randomNo;
    }
}
