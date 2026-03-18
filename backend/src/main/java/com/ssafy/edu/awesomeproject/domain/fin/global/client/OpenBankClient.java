package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankCreateAccountRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankTransactionHistoryRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankTransferRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransactionHistoryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransferResponse;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.request.OpenBankDetailAccountRequest;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response.OpenBankDetailAccountResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface OpenBankClient {
    @PostExchange("/ssafy/api/v1/edu/demandDeposit/createDemandDepositAccount")
    OpenBankCreateAccountResponse fetchCreateDemandDepositAccount(
            @RequestBody OpenBankCreateAccountRequest request);

    @PostExchange("/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountList")
    OpenBankResponse fetchDemandDepositAccounts(@RequestBody OpenBankRequest request);

    @PostExchange("/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccount")
    OpenBankDetailAccountResponse fetchAccountDetail(
            @RequestBody OpenBankDetailAccountRequest request);

    // 카드목록 호출 url
    @PostExchange("/ssafy/api/v1/edu/creditCard/inquireSignUpCreditCardList")
    com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankResponse
            fetchCreditCardList(
                    @RequestBody
                            com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request
                                            .OpenBankRequest
                                    request);

    @PostExchange("/ssafy/api/v1/edu/demandDeposit/inquireTransactionHistoryList")
    OpenBankTransactionHistoryResponse fetchTransactionHistory(
            @RequestBody OpenBankTransactionHistoryRequest request);

    @PostExchange("/ssafy/api/v1/edu/demandDeposit/updateDemandDepositAccountTransfer")
    OpenBankTransferResponse fetchAccountTransfer(@RequestBody OpenBankTransferRequest request);
}
