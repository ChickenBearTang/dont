package com.ssafy.edu.awesomeproject.domain.fin.account.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class AccountListResponse {

    private List<AccountDetail> accounts;

    @Getter
    @Builder
    public static class AccountDetail {
        private String bankName;      // 예: "우리은행"
        private String accountNo;     // 예: "0204667768182760"
        private String accountName;   // 예: "우리 드림하이 통장"
    }
}
