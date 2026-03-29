import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Select, Checkbox, BirthDateField, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import {
  checkEmailAvailability,
  confirmEmailVerificationCode,
  login,
  mapUserProfileFromLogin,
  sendEmailVerificationCode,
  signup,
} from '@/features/auth/api/authApi';
import { fetchCohorts, fetchOnboardingStatus } from '@/features/user/api/userApi';
import type { SignUpRequestPayload } from '@/features/auth/types';
import type { Cohort, SelectOption } from '@/shared/types';


interface FormState {
  success: boolean;
  message: string;
  errors: Record<string, string>;
}

const initialState: FormState = {
  success: false,
  message: '',
  errors: {},
};

export const SignUpForm = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();
  const { loginSuccess } = useAuthStore();
  const [cohortOptions, setCohortOptions] = useState<SelectOption[]>([]);
  const [loadingCohorts, setLoadingCohorts] = useState(true);
  const [state, setState] = useState<FormState>(initialState);
  const [isPending, setIsPending] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [isSendingVerification, setIsSendingVerification] = useState(false);
  const [isConfirmingVerification, setIsConfirmingVerification] = useState(false);
  const [isCheckingEmail, setIsCheckingEmail] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [isEmailAvailable, setIsEmailAvailable] = useState(false);
  const [verificationExpiresIn, setVerificationExpiresIn] = useState(0);
  const [showPassword, setShowPassword] = useState(false);


  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    name: '',
    birthDate: '',
    cohortId: '',
    termsAgreed: false,
  });


  useEffect(() => {
    const loadCohorts = async () => {
      try {
        const response = await fetchCohorts();
        const options = response.data.map((c: Cohort) => ({
          value: c.cohortId,
          label: `${c.generationNo}기`,
        }));
        setCohortOptions(options);
      } catch {
        addToast('기수 목록을 불러오지 못했습니다.', 'error');
      } finally {
        setLoadingCohorts(false);
      }
    };
    loadCohorts();
  }, [addToast]);

  useEffect(() => {
    if (!verificationSent || isEmailVerified || verificationExpiresIn <= 0) {
      return;
    }

    const timer = window.setInterval(() => {
      setVerificationExpiresIn((prev) => {
        if (prev <= 1) {
          window.clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => window.clearInterval(timer);
  }, [verificationSent, isEmailVerified, verificationExpiresIn]);

  const validate = (): FormState => {
    const { email, password, passwordConfirm, name, birthDate, cohortId, termsAgreed } = formData;
    const errors: Record<string, string> = {};
    if (!email.includes('@')) errors.email = '올바른 이메일 형식을 입력해주세요.';
    if (password.length < 8) errors.password = '비밀번호는 8자 이상이어야 합니다.';
    if (!passwordConfirm) errors.passwordConfirm = '비밀번호 확인을 입력해주세요.';
    if (passwordConfirm && password !== passwordConfirm) {
      errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';
    }
    if (!name.trim()) errors.name = '이름을 입력해주세요.';
    if (!birthDate) errors.birthDate = '생년월일을 입력해주세요.';
    if (!cohortId) errors.cohortId = '기수를 선택해주세요.';
    if (!termsAgreed) errors.termsAgreed = '약관에 동의해야 합니다.';
    if (!isEmailAvailable) errors.email = '이메일 중복 확인을 완료해주세요.';
    if (!verificationSent) errors.emailVerification = '이메일 인증 코드를 먼저 발송해주세요.';
    if (!isEmailVerified) errors.emailVerification = '이메일 인증을 완료해주세요.';

    return {
      success: false,
      message: Object.keys(errors).length > 0 ? '입력 정보를 확인해주세요.' : '',
      errors,
    };
  };

  const resetEmailVerificationState = () => {
    setIsEmailAvailable(false);
    setVerificationSent(false);
    setIsEmailVerified(false);
    setVerificationCode('');
    setVerificationExpiresIn(0);
  };

  const handleCheckEmail = async () => {
    if (!formData.email.includes('@')) {
      setState((prev) => ({
        ...prev,
        errors: { ...prev.errors, email: '올바른 이메일 형식을 입력해주세요.' },
      }));
      return;
    }

    setIsCheckingEmail(true);
    try {
      const response = await checkEmailAvailability(formData.email);
      if (response.data.available) {
        setIsEmailAvailable(true);
        setState((prev) => ({
          ...prev,
          errors: { ...prev.errors, email: '' },
        }));
        addToast('사용 가능한 이메일입니다.', 'success');
      } else {
        setIsEmailAvailable(false);
        addToast('이미 사용 중인 이메일입니다.', 'error');
      }
    } catch {
      setIsEmailAvailable(false);
      addToast('이메일 중복 확인에 실패했습니다.', 'error');
    } finally {
      setIsCheckingEmail(false);
    }
  };

  const handleSendVerification = async () => {
    if (!isEmailAvailable) {
      addToast('이메일 중복 확인을 먼저 진행해주세요.', 'error');
      return;
    }

    if (!formData.email.includes('@')) {
      setState((prev) => ({
        ...prev,
        errors: { ...prev.errors, email: '올바른 이메일 형식을 입력해주세요.' },
      }));
      return;
    }

    setIsSendingVerification(true);
    try {
      const response = await sendEmailVerificationCode({ email: formData.email });
      setVerificationSent(true);
      setIsEmailVerified(false);
      setVerificationExpiresIn(response.data.expiresInSeconds);
      addToast('인증 코드를 이메일로 발송했습니다.', 'success');
    } catch {
      addToast('인증 코드 발송에 실패했습니다.', 'error');
    } finally {
      setIsSendingVerification(false);
    }
  };

  const handleConfirmVerification = async () => {
    if (!verificationCode.trim()) {
      setState((prev) => ({
        ...prev,
        errors: { ...prev.errors, emailVerification: '인증 코드를 입력해주세요.' },
      }));
      return;
    }

    setIsConfirmingVerification(true);
    try {
      await confirmEmailVerificationCode({
        email: formData.email,
        code: verificationCode,
      });
      setIsEmailVerified(true);
      setVerificationExpiresIn(0);
      setState((prev) => ({
        ...prev,
        errors: { ...prev.errors, emailVerification: '' },
      }));
      addToast('이메일 인증이 완료되었습니다.', 'success');
    } catch {
      setIsEmailVerified(false);
      addToast('이메일 인증 코드가 올바르지 않거나 만료되었습니다.', 'error');
    } finally {
      setIsConfirmingVerification(false);
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextState = validate();
    setState(nextState);

    if (Object.keys(nextState.errors).length > 0) {
      return;
    }

    setIsPending(true);
    const payload: SignUpRequestPayload = {
      email: formData.email,
      password: formData.password,
      name: formData.name,
      birthDate: formData.birthDate,
      cohortId: Number(formData.cohortId),
      termsAgreed: formData.termsAgreed,
    };

    try {
      await signup(payload);
    } catch {
      addToast('회원가입 중 에러가 발생했습니다.', 'error');
      setIsPending(false);
      return;
    }

    try {
      const loginResponse = await login({
        email: formData.email,
        password: formData.password,
      });

      loginSuccess({
        accessToken: loginResponse.data.accessToken,
        user: mapUserProfileFromLogin(loginResponse.data),
      });
    } catch {
      addToast(
        '회원가입은 완료되었지만 자동 로그인에 실패했습니다. 로그인 후 진행해주세요.',
        'error'
      );
      navigate('/login', { replace: true });
      setIsPending(false);
      return;
    }

    try {
      const onboardingStatusResponse = await fetchOnboardingStatus();
      const onboardingStatus = onboardingStatusResponse.data.onboardingStatus;
      const nextPath =
        onboardingStatus === 'NOT_STARTED'
          ? '/onboarding'
          : onboardingStatus === 'COMPLETED'
            ? '/dashboard'
            : '/finance-connect';
      addToast('회원가입이 완료되었습니다.', 'success');
      navigate(nextPath, { replace: true });
    } catch {
      addToast(
        '회원가입/로그인은 완료되었지만 온보딩 상태 조회에 실패했습니다. 온보딩으로 이동합니다.',
        'error'
      );
      navigate('/onboarding', { replace: true });
    } finally {
      setIsPending(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    if (name === 'email') {
      resetEmailVerificationState();
    }
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleCohortChange = (value: string) => {
    setFormData((prev) => ({ ...prev, cohortId: value }));
  };

  const handleDateChange = (value: string) => {
    setFormData((prev) => ({ ...prev, birthDate: value }));
  };

  const formatRemainingTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainSeconds = seconds % 60;
    return `${minutes}:${String(remainSeconds).padStart(2, '0')}`;
  };

  const passwordHint =
    formData.password.length === 0
      ? undefined
      : formData.password.length >= 8
        ? '사용 가능한 비밀번호입니다.'
        : '비밀번호는 8자 이상이어야 합니다.';

  const passwordHintTone = formData.password.length >= 8 ? 'success' : 'default';
  const passwordLiveError = formData.password.length > 0 && formData.password.length < 8;

  const passwordConfirmHint =
    formData.passwordConfirm.length === 0
      ? undefined
      : formData.password === formData.passwordConfirm
        ? '비밀번호가 일치합니다.'
        : '비밀번호가 일치하지 않습니다.';

  const passwordConfirmHintTone =
    formData.passwordConfirm.length > 0 && formData.password === formData.passwordConfirm
      ? 'success'
      : 'default';
  const passwordConfirmLiveError =
    formData.passwordConfirm.length > 0 && formData.password !== formData.passwordConfirm;

  const eyeButtonClassName =
    'flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-surface-soft';

  const renderPasswordToggle = (visible: boolean, onClick: () => void) => (
    <button
      type="button"
      onClick={onClick}
      className={eyeButtonClassName}
      aria-label={visible ? '비밀번호 숨기기' : '비밀번호 보기'}
    >
      {visible ? (
        <svg
          className="h-4.5 w-4.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18" />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10.584 10.587A2 2 0 0013.413 13.416M9.88 5.09A9.953 9.953 0 0112 4.875c4.478 0 8.268 2.943 9.542 7.003a9.97 9.97 0 01-2.231 3.592M6.228 6.228A9.956 9.956 0 002.458 11.878a9.97 9.97 0 005.365 6.08A9.953 9.953 0 0012 19.125c1.41 0 2.751-.293 3.966-.82"
          />
        </svg>
      ) : (
        <svg
          className="h-4.5 w-4.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
    </button>
  );

  return (
    <form noValidate onSubmit={handleSubmit} className="flex flex-col gap-2">
      <Input
        label="이메일"
        name="email"
        type="email"
        placeholder="example@test.com"
        required
        value={formData.email}
        onChange={handleInputChange}
        error={!!state.errors.email}
        errorMessage={state.errors.email}
      />
      <div className="mt-2">
        <Button
          type="button"
          variant="outline"
          onClick={handleCheckEmail}
          disabled={isCheckingEmail}
        >
          {isCheckingEmail ? '확인 중...' : '이메일 중복 확인'}
        </Button>
      </div>
      {isEmailAvailable && (
        <p className="text-success text-[13px] ml-1 font-medium">사용 가능한 이메일입니다.</p>
      )}
      {isEmailAvailable && (
        <div className="mt-2">
          <Button type="button" onClick={handleSendVerification} disabled={isSendingVerification}>
            {isSendingVerification
              ? '발송 중...'
              : verificationSent
                ? '인증 코드 재발송'
                : '인증 코드 발송'}
          </Button>
        </div>
      )}
      {verificationSent && (
        <>
          <div className="mt-2">
            <Input
              label="인증 코드"
              name="verificationCode"
              placeholder="6자리 인증 코드를 입력하세요"
              value={verificationCode}
              onChange={(event) =>
                setVerificationCode(event.target.value.replace(/[^0-9]/g, '').slice(0, 6))
              }
              error={!!state.errors.emailVerification}
              errorMessage={state.errors.emailVerification}
              className="mt-0"
            />
          </div>
          {!isEmailVerified && verificationExpiresIn > 0 && (
            <p className="text-[13px] ml-1 font-medium text-text-muted">
              남은 시간 {formatRemainingTime(verificationExpiresIn)}
            </p>
          )}
          {!isEmailVerified && verificationExpiresIn === 0 && (
            <p className="text-danger text-[13px] ml-1 font-medium">
              인증 시간이 만료되었습니다. 인증 코드를 다시 발송해주세요.
            </p>
          )}
          <div className="mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleConfirmVerification}
              disabled={isConfirmingVerification || verificationExpiresIn === 0}
            >
              {isConfirmingVerification
                ? '확인 중...'
                : isEmailVerified
                  ? '인증 완료'
                  : '인증 확인'}
            </Button>
          </div>
        </>
      )}
      {isEmailVerified && (
        <p className="text-success text-[13px] ml-1 font-medium">이메일 인증이 완료되었습니다.</p>
      )}

      <Input
        label="비밀번호"
        name="password"
        type={showPassword ? 'text' : 'password'}
        placeholder="8자 이상 입력해주세요"
        required
        value={formData.password}
        onChange={handleInputChange}
        error={!!state.errors.password || passwordLiveError}
        errorMessage={
          state.errors.password ||
          (passwordLiveError ? '비밀번호는 8자 이상이어야 합니다.' : undefined)
        }
        hint={state.errors.password || passwordLiveError ? undefined : passwordHint}
        hintTone={passwordHintTone}
        endAdornment={renderPasswordToggle(showPassword, () => setShowPassword((prev) => !prev))}
      />

      <Input
        label="비밀번호 확인"
        name="passwordConfirm"
        type={showPassword ? 'text' : 'password'}
        placeholder="비밀번호를 다시 입력해주세요"
        required
        value={formData.passwordConfirm}
        onChange={handleInputChange}
        error={!!state.errors.passwordConfirm || passwordConfirmLiveError}
        errorMessage={
          state.errors.passwordConfirm ||
          (passwordConfirmLiveError ? '비밀번호가 일치하지 않습니다.' : undefined)
        }
        hint={
          state.errors.passwordConfirm || passwordConfirmLiveError ? undefined : passwordConfirmHint
        }
        hintTone={passwordConfirmHintTone}
      />

      <Input
        label="이름"
        name="name"
        placeholder="실명을 입력하세요"
        required
        value={formData.name}
        onChange={handleInputChange}
        error={!!state.errors.name}
        errorMessage={state.errors.name}
      />

      <BirthDateField
        label="생년월일"
        name="birthDate"
        value={formData.birthDate}
        max={new Date().toISOString().slice(0, 10)}
        onChange={handleDateChange}
        error={!!state.errors.birthDate}
        errorMessage={state.errors.birthDate}
      />

      <Select
        label="기수"
        name="cohortId"
        placeholder={loadingCohorts ? '기수 정보 로딩 중...' : '기수를 선택하세요'}
        options={cohortOptions}
        searchable
        searchPlaceholder="기수를 검색하세요"
        required
        disabled={loadingCohorts}
        value={formData.cohortId}
        onChange={handleCohortChange}
        error={!!state.errors.cohortId}
        errorMessage={state.errors.cohortId}
      />

      <Checkbox
        label="서비스 이용약관 및 개인정보 처리방침에 동의합니다."
        name="termsAgreed"
        className="mt-6"
        checked={formData.termsAgreed}
        onChange={handleInputChange}
        error={!!state.errors.termsAgreed}
        errorMessage={state.errors.termsAgreed}
      />

      <Button type="submit" className="mt-8" disabled={isPending}>
        {isPending ? '가입 중...' : '회원가입 완료'}
      </Button>
    </form>
  );
};
