package com.ssafy.edu.awesomeproject.domain.fin.account.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.lenient;

import com.ssafy.edu.awesomeproject.domain.auth.entity.User;
import com.ssafy.edu.awesomeproject.domain.auth.repository.UserRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankCreateAccountResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.client.dto.response.OpenBankTransferResponse;
import com.ssafy.edu.awesomeproject.domain.fin.account.dto.request.SaveBoxCreateRequest;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.Account;
import com.ssafy.edu.awesomeproject.domain.fin.account.entity.SavingsSetting;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.AccountTransactionRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.repository.SavingsSettingRepository;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountErrorCode;
import com.ssafy.edu.awesomeproject.domain.fin.account.error.AccountException;
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

    @Mock
    private OpenBankAdapter openBankAdapter;

    @Mock
    private AccountRepository accountRepository;

    @Mock
    private AccountTransactionRepository accountTransactionRepository;

    @Mock
    private SavingsSettingRepository savingsSettingRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private AccountService accountService;

    @Test
    @DisplayName("[시나리오 A] getAccount - 타인 계좌 조회 시 BOLA 방어 (AccountException 발생)")
    void getAccount_BolaDefense() {
        // given
        Long requesterId = 1L;
        Long otherUserId = 999L;
        Long accountId = 100L;
        Account otherAccount = mock(Account.class);
        
        given(otherAccount.getUserId()).willReturn(otherUserId);
        given(accountRepository.findById(accountId)).willReturn(Optional.of(otherAccount));

        // when & then
        AccountException exception = assertThrows(AccountException.class, () -> {
            accountService.getAccount(requesterId, accountId);
        });

        assertEquals(AccountErrorCode.ACCOUNT_NOT_FOUND, exception.getErrorCode());
    }

    @Test
    @DisplayName("[시나리오 B] manualSavings - 정상적인 수동 저축 실행 (성공)")
    void manualSavings_Success() {
        // given
        Long userId = 1L;
        BigDecimal amount = new BigDecimal("10000");
        
        SavingsSetting setting = mock(SavingsSetting.class);
        given(setting.getPrimaryAccountId()).willReturn(10L);
        given(setting.getSaveboxAccountId()).willReturn(20L);
        given(savingsSettingRepository.findByUserIdAndIsActiveTrue(userId)).willReturn(Optional.of(setting));

        Account primaryAccount = mock(Account.class);
        Account saveboxAccount = mock(Account.class);
        given(primaryAccount.getUserId()).willReturn(userId);
        given(primaryAccount.getAccountNo()).willReturn("111-222");
        given(saveboxAccount.getUserId()).willReturn(userId);
        given(saveboxAccount.getAccountNo()).willReturn("333-444");
        
        given(accountRepository.findById(10L)).willReturn(Optional.of(primaryAccount));
        given(accountRepository.findById(20L)).willReturn(Optional.of(saveboxAccount));

        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        OpenBankTransferResponse apiResponse = mock(OpenBankTransferResponse.class);
        OpenBankTransferResponse.Header header = mock(OpenBankTransferResponse.Header.class);
        given(header.getResponseCode()).willReturn("H0000");
        given(apiResponse.getHeader()).willReturn(header);

        given(openBankAdapter.fetchAccountTransfer(anyString(), anyString(), anyString(), anyString(), anyString(), anyString()))
                .willReturn(apiResponse);

        // when
        accountService.manualSavings(userId, amount);

        // then
        verify(openBankAdapter, times(1)).fetchAccountTransfer(
                eq("user-key"),
                eq("333-444"),
                anyString(),
                anyString(),
                eq("111-222"),
                anyString()
        );
    }

    @Test
    @DisplayName("[시나리오 C] createSaveBox - 외부 API 에러 시 AccountException(API_RESPONSE_ERROR) 발생")
    void createSaveBox_ApiError() {
        // given
        Long userId = 1L;
        SaveBoxCreateRequest request = new SaveBoxCreateRequest("unique-no");
        
        User user = mock(User.class);
        given(user.getSsafyFinanceUserKey()).willReturn("user-key");
        given(userRepository.findById(userId)).willReturn(Optional.of(user));

        OpenBankCreateAccountResponse apiResponse = mock(OpenBankCreateAccountResponse.class);
        OpenBankResHeader header = mock(OpenBankResHeader.class);
        given(header.getResponseCode()).willReturn("500"); // 에러 코드
        given(apiResponse.getHeader()).willReturn(header);
        given(apiResponse.getRec()).willReturn(mock(OpenBankCreateAccountResponse.Rec.class));

        given(openBankAdapter.createDemandDepositAccount(anyString(), anyString())).willReturn(apiResponse);

        // when & then
        AccountException exception = assertThrows(AccountException.class, () -> {
            accountService.createSaveBox(userId, request);
        });

        assertEquals(AccountErrorCode.API_RESPONSE_ERROR, exception.getErrorCode());
    }
}
