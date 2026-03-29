package com.ssafy.edu.awesomeproject.domain.fin.global.client;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankCreateAccountRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankTransactionHistoryRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.request.OpenBankTransferRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransactionHistoryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransferResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankReqHeader;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.request.OpenBankDetailAccountRequest;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response.OpenBankDetailAccountResponse;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.ThreadLocalRandom;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class OpenBankAdapter {

    private final OpenBankClient openBankClient;

    @Value("${ssafy.api.key}")
    private String apiKey;


    public OpenBankCreateAccountResponse createDemandDepositAccount(
            String userKey, String accountTypeUniqueNo) {
        OpenBankCreateAccountRequest request =
                createAccountCreationRequest(userKey, accountTypeUniqueNo);
        return openBankClient.fetchCreateDemandDepositAccount(request);
    }

    private OpenBankCreateAccountRequest createAccountCreationRequest(
            String userKey, String accountTypeUniqueNo) {
        LocalDateTime now = LocalDateTime.now();
        return OpenBankCreateAccountRequest.builder()
                .header(
                        OpenBankReqHeader.builder()
                                .apiName("createDemandDepositAccount")
                                .transmissionDate(
                                        now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                                .institutionCode("00100")
                                .fintechAppNo("001")
                                .apiServiceCode("createDemandDepositAccount")
                                .institutionTransactionUniqueNo(generateUniqueNo(now))
                                .apiKey(apiKey)
                                .userKey(userKey)
                                .build())
                .accountTypeUniqueNo(accountTypeUniqueNo)
                .build();
    }

    public AccountListResponse fetchDemandDepositAccounts(String userKey) {

        OpenBankRequest request = createAccountListRequest(userKey);


        OpenBankResponse response = openBankClient.fetchDemandDepositAccounts(request);


        return AccountListResponse.from(response);
    }

    private OpenBankRequest createAccountListRequest(String userKey) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankRequest.builder()
                .header(
                        OpenBankReqHeader.builder()
                                .apiName("inquireDemandDepositAccountList")
                                .transmissionDate(
                                        now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
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

    public OpenBankDetailAccountResponse fetchAccountDetail(String userKey, String accountNo) {

        OpenBankDetailAccountRequest request = createAccountDetailRequest(userKey, accountNo);


        return openBankClient.fetchAccountDetail(request);
    }

    private OpenBankDetailAccountRequest createAccountDetailRequest(
            String userKey, String accountNo) {
        LocalDateTime now = LocalDateTime.now();

        return OpenBankDetailAccountRequest.builder()
                .header(
                        OpenBankReqHeader.builder()
                                .apiName("inquireDemandDepositAccount")
                                .transmissionDate(
                                        now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                                .transmissionTime(now.format(DateTimeFormatter.ofPattern("HHmmss")))
                                .institutionCode("00100")
                                .fintechAppNo("001")
                                .apiServiceCode("inquireDemandDepositAccount")
                                .institutionTransactionUniqueNo(generateUniqueNo(now))
                                .apiKey(apiKey)
                                .userKey(userKey)
                                .build())
                .accountNo(accountNo)
                .build();
    }

    public OpenBankTransactionHistoryResponse fetchTransactionHistory(
            String userKey,
            String accountNo,
            String startDate,
            String endDate,
            String transactionType,
            String orderByType) {
        LocalDateTime now = LocalDateTime.now();
        OpenBankTransactionHistoryRequest request =
                OpenBankTransactionHistoryRequest.builder()
                        .header(
                                OpenBankReqHeader.builder()
                                        .apiName("inquireTransactionHistoryList")
                                        .transmissionDate(
                                                now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                                        .transmissionTime(
                                                now.format(DateTimeFormatter.ofPattern("HHmmss")))
                                        .institutionCode("00100")
                                        .fintechAppNo("001")
                                        .apiServiceCode("inquireTransactionHistoryList")
                                        .institutionTransactionUniqueNo(generateUniqueNo(now))
                                        .apiKey(apiKey)
                                        .userKey(userKey)
                                        .build())
                        .accountNo(accountNo)
                        .startDate(startDate)
                        .endDate(endDate)
                        .transactionType(transactionType)
                        .orderByType(orderByType)
                        .build();

        return openBankClient.fetchTransactionHistory(request);
    }

    public OpenBankTransferResponse fetchAccountTransfer(
            String userKey,
            String depositAccountNo,
            String depositTransactionSummary,
            String transactionBalance,
            String withdrawalAccountNo,
            String withdrawalTransactionSummary) {
        LocalDateTime now = LocalDateTime.now();
        OpenBankTransferRequest request =
                OpenBankTransferRequest.builder()
                        .header(
                                OpenBankReqHeader.builder()
                                        .apiName("updateDemandDepositAccountTransfer")
                                        .transmissionDate(
                                                now.format(DateTimeFormatter.ofPattern("yyyyMMdd")))
                                        .transmissionTime(
                                                now.format(DateTimeFormatter.ofPattern("HHmmss")))
                                        .institutionCode("00100")
                                        .fintechAppNo("001")
                                        .apiServiceCode("updateDemandDepositAccountTransfer")
                                        .institutionTransactionUniqueNo(generateUniqueNo(now))
                                        .apiKey(apiKey)
                                        .userKey(userKey)
                                        .build())
                        .depositAccountNo(depositAccountNo)
                        .depositTransactionSummary(depositTransactionSummary)
                        .transactionBalance(transactionBalance)
                        .withdrawalAccountNo(withdrawalAccountNo)
                        .withdrawalTransactionSummary(withdrawalTransactionSummary)
                        .build();

        return openBankClient.fetchAccountTransfer(request);
    }

    private String generateUniqueNo(LocalDateTime now) {
        String timestamp = now.format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));
        int randomNo = ThreadLocalRandom.current().nextInt(100000, 1000000);
        return timestamp + randomNo;
    }
}
