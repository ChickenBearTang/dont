package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingTargetRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional // DB에 데이터를 저장/수정하므로 트랜잭션 관리가 필수입니다.
public class AccountService {

    private final OpenBankAdapter openBankAdapter;
    private final AccountRepository accountRepository;

    /** '세이브 박스' 계좌를 신규 개설합니다. (Command) */
    public AccountResponse createSaveBox(Long userId, SaveBoxCreateRequest request) {
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767"; // 임시 userKey

        // 1. 외부 API를 통한 실제 계좌 개설
        OpenBankCreateAccountResponse apiResponse =
                openBankAdapter.createDemandDepositAccount(userKey, request.accountTypeUniqueNo());

        if (apiResponse == null || apiResponse.getRec() == null) {
            throw new RuntimeException("계좌 개설에 실패했습니다.");
        }

        OpenBankCreateAccountResponse.Rec rec = apiResponse.getRec();

        // 2. 개설된 계좌 정보를 우리 DB에 저장
        Account newAccount =
                Account.builder()
                        .userId(userId)
                        .accountNo(rec.getAccountNo())
                        .bankName(rec.getBankName())
                        .bankCode(rec.getBankCode())
                        .accountName(rec.getAccountName())
                        .currencyCode(rec.getCurrency())
                        .balance(BigDecimal.ZERO)
                        .status("ACTIVE")
                        .isPrimary(false)
                        .accountRole("SAVE_BOX") // 비상금 용도인 세이브 박스 역할 부여
                        .userName(rec.getUserName())
                        .accountTypeCode(rec.getAccountTypeCode())
                        .accountTypeName(rec.getAccountTypeName())
                        .accountCreatedDate(parseLocalDate(rec.getAccountCreatedDate()))
                        .accountExpiryDate(parseLocalDate(rec.getAccountExpiryDate()))
                        .dailyTransferLimit(new BigDecimal(rec.getDailyTransferLimit()))
                        .oneTimeTransferLimit(new BigDecimal(rec.getOneTimeTransferLimit()))
                        .lastTransactionDate(parseLocalDate(rec.getAccountCreatedDate()))
                        .build();

        Account saved = accountRepository.save(newAccount);

        return AccountResponse.from(saved);
    }

    /** 저축 목표 금액을 설정하거나 변경합니다. (Command) */
    public AccountResponse updateSavingTargetAmount(
            Long userId, Long accountId, SavingTargetRequest request) {
        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        account.updateSavingTargetAmount(request.savingTargetAmount());

        return AccountResponse.from(account);
    }

    /** 사용자의 특정 계좌 상세 정보를 조회합니다. (Query) */
    @Transactional(readOnly = true)
    public AccountResponse getAccount(Long userId, Long accountId) {
        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        return AccountResponse.from(account);
    }

    /** 사용자의 계좌 목록을 조회합니다. 1. 외부 API와 동기화하여 DB를 최신 상태로 만듭니다. 2. 우리 DB에 저장된 계좌 정보를 조회하여 반환합니다. */
    public AccountListResponse getAccountList(Long userId) {
        // 1. 외부 API와 동기화 (Command)
        syncAccounts(userId);

        // 2. DB에서 최신 계좌 목록 조회 (Query)
        List<Account> accounts = accountRepository.findAllByUserId(userId);

        // 3. 조회된 엔티티 목록을 DTO로 변환하여 반환
        List<AccountListResponse.AccountDetail> accountDetails =
                accounts.stream()
                        .map(
                                account ->
                                        new AccountListResponse.AccountDetail(
                                                account.getBankName(),
                                                account.getBankCode(),
                                                account.getAccountNo(),
                                                account.getAccountName(),
                                                String.valueOf(account.getBalance()),
                                                account.getCurrencyCode()))
                        .collect(Collectors.toList());

        return new AccountListResponse(accountDetails);
    }

    /** 외부 API를 통해 계좌 정보를 가져와 DB와 동기화합니다. (Upsert) */
    private void syncAccounts(Long userId) {
        String userKey = "31cc0084-6b77-42c9-8927-762488bc2767"; // 임시 userKey
        AccountListResponse apiResponse = openBankAdapter.fetchDemandDepositAccounts(userKey);

        for (AccountListResponse.AccountDetail listDetail : apiResponse.accounts()) {
            // 상세 정보 조회를 통해 더 풍부한 데이터를 가져옵니다.
            com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response
                            .OpenBankDetailAccountResponse
                    detailResponse =
                            openBankAdapter.fetchAccountDetail(userKey, listDetail.accountNo());

            if (detailResponse == null || detailResponse.rec() == null) {
                continue;
            }

            com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.response
                            .OpenBankDetailAccountResponse.Rec
                    rec = detailResponse.rec();
            Optional<Account> accountOpt = accountRepository.findByAccountNo(rec.accountNo());

            BigDecimal balance = new BigDecimal(rec.accountBalance());
            BigDecimal dailyLimit = new BigDecimal(rec.dailyTransferLimit());
            BigDecimal oneTimeLimit = new BigDecimal(rec.oneTimeTransferLimit());

            if (accountOpt.isPresent()) {
                // 이미 존재하는 계좌는 동적으로 변하는 정보를 업데이트합니다.
                Account existingAccount = accountOpt.get();
                existingAccount.updateDynamicInfo(rec.accountName(), balance, "ACTIVE");
            } else {
                // 새로운 계좌 생성 및 저장
                Account newAccount =
                        Account.builder()
                                .userId(userId)
                                .accountNo(rec.accountNo())
                                .bankName(rec.bankName())
                                .bankCode(rec.bankCode())
                                .accountName(rec.accountName())
                                .currencyCode(rec.currency())
                                .balance(
                                        BigDecimal.ZERO) // 상세 조회 시점의 잔액은 아래에서 바로 갱신될 수 있으나 builder에
                                // 포함
                                .status("ACTIVE")
                                .isPrimary(false)
                                .accountRole("LINKED_DEPOSIT")
                                .userName(rec.userName())
                                .accountTypeCode(rec.accountTypeCode())
                                .accountTypeName(rec.accountTypeName())
                                .accountCreatedDate(parseLocalDate(rec.accountCreatedDate()))
                                .accountExpiryDate(parseLocalDate(rec.accountExpiryDate()))
                                .dailyTransferLimit(dailyLimit)
                                .oneTimeTransferLimit(oneTimeLimit)
                                .lastTransactionDate(parseLocalDate(rec.lastTransactionDate()))
                                .build();

                // 빌더에서 누락될 수 있는 balance 보정 (updateDynamicInfo 등을 활용 가능하지만 여기서는 builder 완성에 집중)
                newAccount.updateDynamicInfo(rec.accountName(), balance, "ACTIVE");
                accountRepository.save(newAccount);
            }
        }
    }

    private java.time.LocalDate parseLocalDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }
        try {
            return java.time.LocalDate.parse(
                    dateStr, java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        } catch (Exception e) {
            return null;
        }
    }

    /** 특정 계좌를 사용자의 '주 계좌'로 설정합니다. (Command) */
    public AccountResponse setPrimaryAccount(Long userId, Long accountId) {
        // 1. 기존 주 계좌가 있다면 해제
        java.util.List<Account> primaryAccounts =
                accountRepository.findAll().stream()
                        .filter(a -> a.getUserId().equals(userId) && a.isPrimary())
                        .toList();

        for (Account a : primaryAccounts) {
            a.unsetPrimary();
        }

        // 2. 새로운 주 계좌 설정
        Account account =
                accountRepository
                        .findById(accountId)
                        .filter(a -> a.getUserId().equals(userId))
                        .orElseThrow(() -> new IllegalArgumentException("계좌를 찾을 수 없습니다."));

        account.setAsPrimary();

        return AccountResponse.from(account);
    }
}
