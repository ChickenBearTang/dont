const defaultMessages = {
  emailVerificationSend: '인증 코드 발송에 실패했습니다.',
  emailVerificationConfirm: '이메일 인증에 실패했습니다.',
  passwordResetRequest: '재설정 코드 요청에 실패했습니다.',
  passwordResetConfirm: '비밀번호 재설정에 실패했습니다.',
} as const;

type ErrorMessageContext = keyof typeof defaultMessages;

export const mapAuthErrorMessage = (
  code: string | undefined,
  context: ErrorMessageContext
): string => {
  if (context === 'emailVerificationSend') {
    if (code === 'AUTH_429_1') {
      return '인증 코드 발송 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.';
    }
    if (code === 'AUTH_502_1') {
      return '메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.';
    }
    if (code === 'COMMON_400_2') {
      return '이메일 형식을 확인해주세요.';
    }
  }

  if (context === 'emailVerificationConfirm') {
    if (code === 'AUTH_400_3') {
      return '인증 코드가 올바르지 않습니다.';
    }
    if (code === 'AUTH_400_4') {
      return '인증 코드가 만료되었습니다. 다시 발송해주세요.';
    }
    if (code === 'AUTH_429_2') {
      return '이메일 인증 시도 횟수를 초과했습니다. 인증 코드를 다시 발송해주세요.';
    }
  }

  if (context === 'passwordResetRequest') {
    if (code === 'AUTH_429_3') {
      return '비밀번호 재설정 코드 요청 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.';
    }
    if (code === 'AUTH_502_1') {
      return '메일 발송에 실패했습니다. 잠시 후 다시 시도해주세요.';
    }
    if (code === 'COMMON_400_2') {
      return '이메일 형식을 확인해주세요.';
    }
  }

  if (context === 'passwordResetConfirm') {
    if (code === 'AUTH_400_5') {
      return '재설정 코드가 올바르지 않습니다.';
    }
    if (code === 'AUTH_400_6') {
      return '재설정 코드가 만료되었습니다. 다시 요청해주세요.';
    }
    if (code === 'AUTH_429_4') {
      return '비밀번호 재설정 인증 시도 횟수를 초과했습니다. 코드를 다시 요청해주세요.';
    }
    if (code === 'COMMON_400_2') {
      return '입력값을 다시 확인해주세요.';
    }
  }

  return defaultMessages[context];
};
