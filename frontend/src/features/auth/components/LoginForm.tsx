import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Input, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { login, mapUserProfileFromLogin } from '@/features/auth/api/authApi';

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

      addToast('로그인에 성공했습니다.', 'success');
      navigate('/dashboard', { replace: true });
    } catch {
      addToast('로그인에 실패했습니다. 이메일/비밀번호를 확인해주세요.', 'error');
    } finally {
      setIsPending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        label="이메일"
        name="email"
        type="email"
        placeholder="example@test.com"
        required
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={!!errors.email}
      />
      {errors.email && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{errors.email}</p>
      )}

      <Input
        label="비밀번호"
        name="password"
        type="password"
        placeholder="비밀번호를 입력하세요"
        required
        value={password}
        onChange={(event) => setPassword(event.target.value)}
        error={!!errors.password}
      />
      {errors.password && (
        <p className="text-error-red text-[13px] ml-1 font-medium">{errors.password}</p>
      )}

      <Button type="submit" className="mt-8" disabled={isPending}>
        {isPending ? '로그인 중...' : '로그인'}
      </Button>
    </form>
  );
};
