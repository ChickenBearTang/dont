import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Input, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { login, mapUserProfileFromLogin } from '@/features/auth/api/authApi';
import { fetchOnboardingStatus } from '@/features/user/api/userApi';

interface FormErrors {
  email?: string;
  password?: string;
}

export const LoginForm = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();
  const { loginSuccess } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});
  const [isPending, setIsPending] = useState(false);

  const validate = (): FormErrors => {
    const nextErrors: FormErrors = {};

    if (!email.includes('@')) {
      nextErrors.email = '올바른 이메일 형식을 입력해주세요.';
    }

    if (!password) {
      nextErrors.password = '비밀번호를 입력해주세요.';
    } else if (password.length < 8) {
      nextErrors.password = '비밀번호는 8자 이상이어야 합니다.';
    }

    return nextErrors;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validate();
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsPending(true);

    try {
      const response = await login({ email, password });
      const loginData = response.data;

      loginSuccess({
        accessToken: loginData.accessToken,
        user: mapUserProfileFromLogin(loginData),
      });
    } catch {
      addToast('로그인에 실패했습니다. 이메일/비밀번호를 확인해주세요.', 'error');
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

      addToast('로그인에 성공했습니다.', 'success');
      navigate(nextPath, { replace: true });
    } catch {
      addToast(
        '로그인은 성공했지만 온보딩 상태를 확인하지 못했습니다. 온보딩으로 이동합니다.',
        'error'
      );
      navigate('/onboarding', { replace: true });
    } finally {
      setIsPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <Input
        label="이메일"
        name="email"
        type="email"
        placeholder="이메일을 입력하세요."
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={!!errors.email}
        errorMessage={errors.email}
      />

      <Input
        label="비밀번호"
        name="password"
        type="password"
        placeholder="비밀번호를 입력하세요."
        required
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={!!errors.password}
        errorMessage={errors.password}
      />

      <div className="-mt-1 text-right">
        <button
          type="button"
          className="text-[13px] font-bold text-accent hover:underline"
          onClick={() => navigate('/forgot-password')}
        >
          비밀번호 찾기
        </button>
      </div>

      <Button type="submit" className="mt-6" disabled={isPending}>
        {isPending ? '로그인 중...' : '로그인'}
      </Button>
    </form>
  );
};
