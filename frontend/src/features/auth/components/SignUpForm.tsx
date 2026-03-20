import { useActionState, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, Select, Checkbox, DatePicker, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { mockDb } from '@/shared/api/mockDb';
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
  const [cohortOptions, setCohortOptions] = useState<SelectOption[]>([]);
  const [loadingCohorts, setLoadingCohorts] = useState(true);

  // --- Controlled Form State ---
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    realName: '',
    nickname: '',
    birthDate: '',
    cohortId: 0,
    termsAgreed: false,
  });

  // 기수 정보 불러오기
  useEffect(() => {
    const loadCohorts = async () => {
      const options = mockDb.getCohorts().map((c: Cohort) => ({
        value: c.cohortId,
        label: c.cohortCode,
      }));
      setCohortOptions(options);
      setLoadingCohorts(false);
    };
    loadCohorts();
  }, []);

  const [state, formAction, isPending] = useActionState(async (): Promise<FormState> => {
    const { email, password, realName, nickname, birthDate, cohortId, termsAgreed } = formData;

    const errors: Record<string, string> = {};
    if (!email.includes('@')) errors.email = '올바른 이메일 형식을 입력해주세요.';
    if (password.length < 8) errors.password = '비밀번호는 8자 이상이어야 합니다.';
    if (!cohortId) errors.cohortId = '기수를 선택해주세요.';
    if (!termsAgreed) errors.termsAgreed = '약관에 동의해야 합니다.';

    if (Object.keys(errors).length > 0) {
      return { success: false, message: '입력 정보를 확인해주세요.', errors };
    }

    try {
      const payload: SignUpRequestPayload = {
        email,
        password,
        realName,
        nickname,
        birthDate,
        cohortId,
        termsAgreed,
      };

      // Prototyping: Mock DB 연동
      await new Promise((resolve) => setTimeout(resolve, 800));
      mockDb.registerUser(payload);
      console.log('User registered in Mock DB:', email);

      return { success: true, message: '회원가입이 완료되었습니다!', errors: {} };
    } catch (error: unknown) {
      console.error('Signup error:', error);
      return {
        success: false,
        message: '회원가입 중 에러가 발생했습니다.',
        errors: {},
      };
    }
  }, initialState);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
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
      navigate('/login');
    } else if (state.message && !state.success) {
      addToast(state.message, 'error');
    }
  }, [state, navigate, addToast]);

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
        label="이름"
        name="realName"
        placeholder="실명을 입력하세요"
        required
        value={formData.realName}
        onChange={handleInputChange}
      />

      <Input
        label="닉네임"
        name="nickname"
        placeholder="사용할 닉네임을 입력하세요"
        required
        value={formData.nickname}
        onChange={handleInputChange}
      />

      <DatePicker
        label="생년월일"
        name="birthDate"
        required
        value={formData.birthDate}
        onChange={handleDateChange}
      />

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
