package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.nullable;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransactionHistoryResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransferResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SavingsSettingRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountListResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.response.AccountTransactionResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.OpenBankAdapter;
import com.ssafy.edu.awesomeproject.domain.fin.global.client.dto.OpenBankResHeader;
import java.math.BigDecimal;
import java.util.Optional;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class AccountServiceTest {

    @Mock private OpenBankAdapter openBankAdapter;

    @Mock private AccountRepository accountRepository;

    @Mock private AccountTransactionRepository accountTransactionRepository;

    @Mock private SavingsSettingRepository savingsSettingRepository;

    @Mock private UserRepository userRepository;

    @Mock private org.springframework.context.ApplicationEventPublisher eventPublisher;

    @InjectMocks private AccountService accountService;

    @Test
    @DisplayName("[시나리오 A] getAccount - 타인 계좌 조회 시 BOLA 방어 (AccountException 발생)")
    void getAccount_BolaDefense() {

        Long requesterId = 1L;
        Long otherUserId = 999L;
        Long accountId = 100L;
        Account otherAccount = mock(Account.class);

        given(otherAccount.getUserId()).willReturn(otherUserId);
        given(accountRepository.findById(accountId)).willReturn(Optional.of(otherAccount));


        AccountException exception =
                assertThrows(
                        AccountException.class,
                        () -> {
                            accountService.getAccount(requesterId, accountId);
                        });

        assertEquals(AccountErrorCode.ACCOUNT_NOT_FOUND, exception.getErrorCode());
    }

    @Test
    @DisplayName("[시나리오 B] manualSavings - 정상적인 수동 저축 실행 (성공)")
    void manualSavings_Success() {

        Long userId = 1L;
        BigDecimal amount = new BigDecimal("10000");

        SavingsSetting setting = mock(SavingsSetting.class);
        given(setting.getPrimaryAccountId()).willReturn(10L);
        given(setting.getSaveboxAccountId()).willReturn(20L);
        given(savingsSettingRepository.findByUserIdAndIsActiveTrue(userId))
                .willReturn(Optional.of(setting));

        Account primaryAccount = mock(Account.class);
        Account saveboxAccount = mock(Account.class);
        given(primaryAccount.getUserId()).willReturn(userId);
        given(primaryAccount.getAccountNo()).willReturn("111-222");
        given(saveboxAccount.getUserId()).willReturn(userId);
        given(saveboxAccount.getId()).willReturn(20L);
        given(saveboxAccount.getAccountNo()).willReturn("333-444");
        given(saveboxAccount.getBalance()).willReturn(new BigDecimal("10000"));

        given(accountRepository.findById(10L)).willReturn(Optional.of(primaryAccount));
        given(accountRepository.findById(20L)).willReturn(Optional.of(saveboxAccount));

        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        OpenBankTransferResponse apiResponse = mock(OpenBankTransferResponse.class);
        OpenBankTransferResponse.Header header = mock(OpenBankTransferResponse.Header.class);
        given(header.getResponseCode()).willReturn("H0000");
        given(apiResponse.getHeader()).willReturn(header);

        given(
                        openBankAdapter.fetchAccountTransfer(
                                anyString(),
                                anyString(),
                                anyString(),
                                anyString(),
                                anyString(),
                                anyString()))
                .willReturn(apiResponse);


        accountService.manualSavings(userId, amount, "password123!");


        verify(openBankAdapter, times(1))
                .fetchAccountTransfer(
                        eq("user-key"),
                        eq("333-444"),
                        anyString(),
                        anyString(),
                        eq("111-222"),
                        anyString());
    }

    @Test
    @DisplayName("[시나리오 C] createSaveBox - 외부 API 에러 시 AccountException(API_RESPONSE_ERROR) 발생")
    void createSaveBox_ApiError() {

        Long userId = 1L;
        SaveBoxCreateRequest request = new SaveBoxCreateRequest("unique-no");

        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        OpenBankCreateAccountResponse apiResponse = mock(OpenBankCreateAccountResponse.class);
        OpenBankResHeader header = mock(OpenBankResHeader.class);
        given(header.getResponseCode()).willReturn("500");
        given(apiResponse.getHeader()).willReturn(header);
        given(apiResponse.getRec()).willReturn(mock(OpenBankCreateAccountResponse.Rec.class));

        given(openBankAdapter.createDemandDepositAccount(anyString(), anyString()))
                .willReturn(apiResponse);


        AccountException exception =
                assertThrows(
                        AccountException.class,
                        () -> {
                            accountService.createSaveBox(userId, request);
                        });

        assertEquals(AccountErrorCode.API_RESPONSE_ERROR, exception.getErrorCode());
    }

    @Test
    @DisplayName("getAccountList - 데이터가 있는 경우 성공")
    void getAccountList_Success_WithData() {

        Long userId = 1L;
        Account account1 = mock(Account.class);
        Account account2 = mock(Account.class);
        given(accountRepository.findAllByUserId(userId))
                .willReturn(java.util.List.of(account1, account2));


        AccountListResponse response = accountService.getAccountList(userId);


        assertEquals(2, response.accounts().size());
        verify(accountRepository, times(1)).findAllByUserId(userId);
    }

    @Test
    @DisplayName("getAccountList - 데이터가 없는 경우 빈 리스트 반환")
    void getAccountList_Success_Empty() {

        Long userId = 1L;
        given(accountRepository.findAllByUserId(userId))
                .willReturn(java.util.Collections.emptyList());


        AccountListResponse response = accountService.getAccountList(userId);


        assertEquals(0, response.accounts().size());
        verify(accountRepository, times(1)).findAllByUserId(userId);
    }

    @Test
    @DisplayName("getAccount - 정상적인 내 계좌 상세 조회 성공")
    void getAccount_Success() {

        Long userId = 1L;
        Long accountId = 100L;
        Account account = mock(Account.class);
        given(account.getUserId()).willReturn(userId);
        given(accountRepository.findById(accountId)).willReturn(Optional.of(account));


        accountService.getAccount(userId, accountId);


        verify(accountRepository, times(1)).findById(accountId);
    }

    @Test
    @DisplayName("refreshAccountList - 오픈뱅킹 연동을 통한 동기화 성공")
    void refreshAccountList_Success() {

        Long userId = 1L;
        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        AccountListResponse.AccountDetail detail =
                new AccountListResponse.AccountDetail(
                        1L,
                        "bank-code",
                        "bank-name",
                        "user-name",
                        "123-456",
                        "account-name",
                        "type-code",
                        "type-name",
                        "20240101",
                        "20250101",
                        "1000",
                        "1000",
                        "5000",
                        "20240101",
                        "KRW",
                        false);
        AccountListResponse apiResponse = new AccountListResponse(java.util.List.of(detail));
        given(openBankAdapter.fetchDemandDepositAccounts("user-key")).willReturn(apiResponse);
        given(accountRepository.findByAccountNo("123-456")).willReturn(Optional.empty());


        accountService.refreshAccountList(userId);


        verify(openBankAdapter, times(1)).fetchDemandDepositAccounts("user-key");
        verify(accountRepository, times(1)).save(any(Account.class));
    }

    @Test
    @DisplayName("setPrimaryAccount - 주계좌 설정 및 기존 주계좌 해제 성공")
    void setPrimaryAccount_Success() {

        Long userId = 1L;
        Long accountId = 100L;

        Account oldPrimary = mock(Account.class);
        given(oldPrimary.isPrimary()).willReturn(true);
        given(accountRepository.findAllByUserId(userId)).willReturn(java.util.List.of(oldPrimary));

        Account newPrimary = mock(Account.class);
        given(newPrimary.getUserId()).willReturn(userId);
        given(accountRepository.findById(accountId)).willReturn(Optional.of(newPrimary));

        SavingsSetting setting = mock(SavingsSetting.class);
        given(savingsSettingRepository.findByUserIdAndIsActiveTrue(userId))
                .willReturn(Optional.of(setting));


        accountService.setPrimaryAccount(userId, accountId);


        verify(oldPrimary, times(1)).unsetPrimary();
        verify(newPrimary, times(1)).setAsPrimary();
        verify(setting, times(1)).updatePrimaryAccount(accountId);
    }

    @Test
    @DisplayName("getAccountTransactions - 검색 기간 내 거래 내역 조회 성공")
    void getAccountTransactions_Success_WithData() {

        Long userId = 1L;
        Long accountId = 100L;
        Account account = mock(Account.class);
        given(account.getUserId()).willReturn(userId);
        given(account.getAccountNo()).willReturn("123-456");
        given(accountRepository.findById(accountId)).willReturn(Optional.of(account));

        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        OpenBankTransactionHistoryResponse apiResponse =
                mock(OpenBankTransactionHistoryResponse.class);
        given(
                        openBankAdapter.fetchTransactionHistory(
                                eq("user-key"),
                                eq("123-456"),
                                anyString(),
                                anyString(),
                                anyString(),
                                anyString()))
                .willReturn(apiResponse);


        OpenBankTransactionHistoryResponse.Rec rec =
                mock(OpenBankTransactionHistoryResponse.Rec.class);
        given(apiResponse.getRec()).willReturn(rec);
        given(rec.getList()).willReturn(java.util.Collections.emptyList());


        accountService.getAccountTransactions(userId, accountId, "20240101", "20240131");


        verify(openBankAdapter, times(1))
                .fetchTransactionHistory(
                        eq("user-key"),
                        eq("123-456"),
                        anyString(),
                        anyString(),
                        anyString(),
                        anyString());
        verify(accountTransactionRepository, times(1))
                .findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                        eq(accountId), any(), any());
    }

    @Test
    @DisplayName("getAccountTransactions - 검색 기간 내 거래 내역이 없는 경우 빈 리스트 반환")
    void getAccountTransactions_Success_Empty() {

        Long userId = 1L;
        Long accountId = 100L;
        Account account = mock(Account.class);
        given(account.getUserId()).willReturn(userId);
        given(accountRepository.findById(accountId)).willReturn(Optional.of(account));

        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        given(
                        openBankAdapter.fetchTransactionHistory(
                                anyString(),
                                nullable(String.class),
                                anyString(),
                                anyString(),
                                anyString(),
                                anyString()))
                .willReturn(null);

        given(
                        accountTransactionRepository
                                .findAllByAccountIdAndTransactionDateBetweenOrderByTransactionDateDescTransactionTimeDesc(
                                        eq(accountId), any(), any()))
                .willReturn(java.util.Collections.emptyList());


        AccountTransactionResponse response =
                accountService.getAccountTransactions(userId, accountId, "20240101", "20240131");


        assertEquals(0, response.transactions().size());
    }

    @Test
    @DisplayName("getSavingsSetting - 설정 정보 조회 성공")
    void getSavingsSetting_Success() {

        Long userId = 1L;
        SavingsSetting setting = mock(SavingsSetting.class);
        given(savingsSettingRepository.findByUserIdAndIsActiveTrue(userId))
                .willReturn(Optional.of(setting));


        accountService.getSavingsSetting(userId);


        verify(savingsSettingRepository, times(1)).findByUserIdAndIsActiveTrue(userId);
    }

    @Test
    @DisplayName("createOrUpdateSavingsSetting - 설정 저장 및 계좌 소유권 검증 성공")
    void createOrUpdateSavingsSetting_Success() {

        Long userId = 1L;
        SavingsSettingRequest request =
                new SavingsSettingRequest(10L, 20L, "월급", new BigDecimal("10000"), true);

        Account primary = mock(Account.class);
        Account savebox = mock(Account.class);
        given(primary.getUserId()).willReturn(userId);
        given(savebox.getUserId()).willReturn(userId);
        given(accountRepository.findById(10L)).willReturn(Optional.of(primary));
        given(accountRepository.findById(20L)).willReturn(Optional.of(savebox));

        given(savingsSettingRepository.findByUserIdAndIsActiveTrue(userId))
                .willReturn(Optional.empty());
        given(savingsSettingRepository.save(any(SavingsSetting.class)))
                .willAnswer(i -> i.getArgument(0));


        accountService.createOrUpdateSavingsSetting(userId, request);


        verify(accountRepository, times(1)).findById(10L);
        verify(accountRepository, times(1)).findById(20L);
        verify(savingsSettingRepository, times(1)).save(any(SavingsSetting.class));
    }
}
