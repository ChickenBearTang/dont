import { useActionState, useEffect, useState } from 'react';
import axios from 'axios';
import { Input, Select, Checkbox, DatePicker, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { signup } from '@/features/auth/api/authApi';
import { fetchCohorts } from '@/features/user/api/userApi';
import type { SignUpRequestPayload } from '@/features/auth/types';
import type { SelectOption } from '@/shared/types';

const EMAIL_REGEX = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/;
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,72}$/;
const DEFAULT_SIGNUP_ERROR_MESSAGE = '회원가입 중 에러가 발생했습니다.';

type SignupErrorResponse = {
  message?: string;
  details?: unknown;
  data?: unknown;
};

const extractDetailMessage = (detail: unknown): string | undefined => {
  if (typeof detail === 'string') {
    return detail;
  }

  if (typeof detail === 'object' && detail !== null) {
    const reason =
      'reason' in detail && typeof detail.reason === 'string' ? detail.reason : undefined;
    const message =
      'message' in detail && typeof detail.message === 'string' ? detail.message : undefined;

    return reason || message;
  }

  return undefined;
};

const extractSignupErrorMessage = (error: unknown): string => {
  if (!axios.isAxiosError(error)) {
    return DEFAULT_SIGNUP_ERROR_MESSAGE;
  }

  const responseData = error.response?.data as SignupErrorResponse | undefined;
  if (!responseData) {
    return DEFAULT_SIGNUP_ERROR_MESSAGE;
  }

  if (responseData.message) {
    return responseData.message;
  }

  const detailSource = responseData.details ?? responseData.data;
  if (Array.isArray(detailSource) && detailSource.length > 0) {
    return extractDetailMessage(detailSource[0]) || DEFAULT_SIGNUP_ERROR_MESSAGE;
  }

  return extractDetailMessage(detailSource) || DEFAULT_SIGNUP_ERROR_MESSAGE;
};

/**
 * 회원가입 결과 상태
 */
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
  const { addToast } = useUIStore();
  const [cohortOptions, setCohortOptions] = useState<SelectOption[]>([]);
  const [loadingCohorts, setLoadingCohorts] = useState(true);

  // --- Controlled Form State ---
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    name: '',
    nickname: '',
    birthDate: '',
    cohortId: 0,
    termsAgreed: false,
  });

  // 기수 정보 불러오기
  useEffect(() => {
    const loadCohorts = async () => {
      try {
        const cohortResponse = await fetchCohorts();
        const options = (cohortResponse.data ?? []).map((cohort) => ({
          value: cohort.cohortId,
          label: cohort.cohortCode,
        }));
        setCohortOptions(options);
      } catch (error) {
        console.error('Cohort load error:', error);
        addToast('기수 정보를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.', 'error');
      } finally {
        setLoadingCohorts(false);
      }
    };
    loadCohorts();
  }, [addToast]);

  /**
   * React 19 useActionState 핸들러
   */
  const [state, formAction, isPending] = useActionState(
    async (_prevState: FormState, _fd: FormData): Promise<FormState> => {
      void _prevState;
      void _fd;

      const { email, password, passwordConfirm, name, nickname, birthDate, cohortId, termsAgreed } =
        formData;

      const errors: Record<string, string> = {};

      if (!EMAIL_REGEX.test(email)) {
        errors.email = '이메일은 영문 소문자 형식으로 입력해주세요.';
      }
      if (!PASSWORD_REGEX.test(password))
        errors.password =
          '비밀번호는 영문 대/소문자, 숫자, 특수문자를 포함해 8자 이상 72자 이하여야 합니다.';
      if (!passwordConfirm) {
        errors.passwordConfirm = '비밀번호 확인을 입력해주세요.';
      } else if (password !== passwordConfirm) {
        errors.passwordConfirm = '비밀번호가 일치하지 않습니다.';
      }
      if (!name) errors.name = '이름을 입력해주세요.';
      if (!nickname) errors.nickname = '닉네임을 입력해주세요.';
      if (!birthDate) errors.birthDate = '생년월일을 입력해주세요.';
      if (!cohortId) errors.cohortId = '기수를 선택해주세요.';
      if (!termsAgreed) errors.termsAgreed = '약관에 동의해야 합니다.';

      if (Object.keys(errors).length > 0) {
        return { success: false, message: '입력 정보를 확인해주세요.', errors };
      }

      try {
        const payload: SignUpRequestPayload = {
          email,
          password,
          name,
          nickname,
          birthDate,
          cohortId,
          termsAgreed,
        };

        const signupResponse = await signup(payload);
        const verificationToken = signupResponse.data?.verificationToken;
        const tokenMessage =
          verificationToken && typeof verificationToken === 'string'
            ? ` 인증 토큰: ${verificationToken}`
            : '';

        return {
          success: true,
          message: `회원가입이 완료되었습니다. 이메일 인증 후 로그인해주세요.${tokenMessage}`,
          errors: {},
        };
      } catch (error: unknown) {
        console.error('Signup error:', error);

        return {
          success: false,
          message: extractSignupErrorMessage(error),
          errors: {},
        };
      }
    },
    initialState
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const normalizedValue = name === 'email' ? value.toLowerCase() : value;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : normalizedValue,
    }));
  };

  const handleCohortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, cohortId: Number(e.target.value) }));
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, birthDate: e.target.value }));
  };

  // 성공 시 이동 및 토스트
  useEffect(() => {
    if (state.success) {
      addToast(state.message, 'success');
    } else if (state.message && !state.success) {
      addToast(state.message, 'error');
    }
  }, [state, addToast]);

  return (
    <form action={formAction} className="flex flex-col gap-2">
      <Input
        label="이메일"
        name="email"
        type="email"
        placeholder="example@test.com"
        required
        value={formData.email}
        onChange={handleInputChange}
        error={!!state.errors.email}
      />
      {state.errors.email && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.email}</p>
      )}

      <Input
        label="비밀번호"
        name="password"
        type="password"
        placeholder="8자 이상 입력해주세요"
        required
        value={formData.password}
        onChange={handleInputChange}
        error={!!state.errors.password}
      />
      {state.errors.password && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.password}</p>
      )}

      <Input
        label="비밀번호 확인"
        name="passwordConfirm"
        type="password"
        placeholder="비밀번호를 다시 입력해주세요"
        required
        value={formData.passwordConfirm}
        onChange={handleInputChange}
        error={!!state.errors.passwordConfirm}
      />
      {state.errors.passwordConfirm && (
        <p className="text-error-red text-[13px] ml-1 font-medium">
          {state.errors.passwordConfirm}
        </p>
      )}

      <Input
        label="이름"
        name="name"
        placeholder="실명을 입력하세요"
        required
        value={formData.name}
        onChange={handleInputChange}
        error={!!state.errors.name}
      />
      {state.errors.name && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.name}</p>
      )}

      <Input
        label="닉네임"
        name="nickname"
        placeholder="사용할 닉네임을 입력하세요"
        required
        value={formData.nickname}
        onChange={handleInputChange}
        error={!!state.errors.nickname}
      />
      {state.errors.nickname && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.nickname}</p>
      )}

      <DatePicker
        label="생년월일"
        name="birthDate"
        required
        value={formData.birthDate}
        onChange={handleDateChange}
      />
      {state.errors.birthDate && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.birthDate}</p>
      )}

      <Select
        label="기수"
        name="cohortId"
        placeholder={loadingCohorts ? '기수 정보 로딩 중...' : '기수를 선택하세요'}
        options={cohortOptions}
        required
        disabled={loadingCohorts}
        value={formData.cohortId}
        onChange={handleCohortChange}
        error={!!state.errors.cohortId}
      />
      {state.errors.cohortId && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.cohortId}</p>
      )}

      <Checkbox
        label="서비스 이용약관 및 개인정보 처리방침에 동의합니다."
        name="termsAgreed"
        className="mt-6"
        checked={formData.termsAgreed}
        onChange={handleInputChange}
      />
      {state.errors.termsAgreed && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.termsAgreed}</p>
      )}

      <Button type="submit" className="mt-8" disabled={isPending}>
        {isPending ? '가입 중...' : '회원가입 완료'}
      </Button>
    </form>
  );
};
