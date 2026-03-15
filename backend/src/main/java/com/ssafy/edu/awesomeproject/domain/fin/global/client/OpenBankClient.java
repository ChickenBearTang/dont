package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankCardTransactionRequest;
import com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankCardTransactionResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface OpenBankClient {
    @PostExchange("/ssafy/api/v1/edu/demandDeposit/inquireDemandDepositAccountList")
    OpenBankResponse fetchDemandDepositAccounts(@RequestBody OpenBankRequest request);

    //카드목록 호출 url
    @PostExchange("/ssafy/api/v1/edu/creditCard/inquireSignUpCreditCardList")
    com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.response.OpenBankResponse fetchCreditCardList(
        @RequestBody com.ssafy.edu.awesomeproject.domain.fin.card.client.dto.request.OpenBankRequest request);

    //카드 거래내역 호출 url
    @PostExchange("/ssafy/api/v1/edu/creditCard/inquireCreditCardTransactionList")
    OpenBankCardTransactionResponse fetchCreditCardTransactions(
        @RequestBody OpenBankCardTransactionRequest request);
}
