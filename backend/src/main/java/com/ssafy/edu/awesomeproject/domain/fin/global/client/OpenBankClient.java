package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface OpenBankClient {
    @PostExchange("/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountList")
    OpenBankResponse fetchDemandDepositAccounts(@RequestBody OpenBankRequest request);
}
