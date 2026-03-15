package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class FinService {

    private final OpenBankAdapter openBankAdapter;

    public AccountListResponse getAccountList(Long userId) {
        // 1. 유저 키 조회 (임시. 차후 수정해서 DB에서 해당 userId의 userKey를 가져와야 함)
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767";

        // 2. Adapter를 통해 외부 API와 통신.
        // Service는 '어떻게' 통신하는지 모르고, '무엇을' 원하는지만 전달합니다.
        return openBankAdapter.fetchDemandDepositAccounts(userKey);
    }
}
