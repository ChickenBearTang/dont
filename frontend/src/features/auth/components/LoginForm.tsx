import { useActionState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { Input, Button } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { mockDb } from '@/shared/api/mockDb';
import type { LoginResponseData } from '@/features/auth/types';

/**
 * 로그인 액션 결과 상태
 */
interface LoginFormState {
  success: boolean;
  message: string;
  data: LoginResponseData | null;
  errors: Record<string, string>;
}

const initialState: LoginFormState = {
  success: false,
  message: '',
  data: null,
  errors: {},
};

export const LoginForm = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();
  const { loginSuccess } = useAuthStore();

  const [state, formAction, isPending] = useActionState(
    async (_prevState: LoginFormState, formData: FormData): Promise<LoginFormState> => {
      const email = formData.get('email') as string;
      const password = formData.get('password') as string;

      // 클라이언트 유효성 검사
      const errors: Record<string, string> = {};
      if (!email.includes('@')) errors.email = '올바른 이메일 형식을 입력해주세요.';
      if (!password) errors.password = '비밀번호를 입력해주세요.';

      if (Object.keys(errors).length > 0) {
        return { ...initialState, errors };
      }

      try {
        // Prototyping: Mock DB 연동
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const user = mockDb.findUser(email);

        if (user) {
          return {
            success: true,
            message: '로그인에 성공했습니다.',
            data: user,
            errors: {},
          };
        }

        return {
          success: false,
          message: '존재하지 않는 계정이거나 비밀번호가 틀렸습니다.',
          data: null,
          errors: {},
        };
      } catch (error: any) {
        return {
          success: false,
          message: '로그인 중 에러가 발생했습니다.',
          data: null,
          errors: {}
        };
      }
    },
    initialState
  );

  // 로그인 성공 시 로직
  useEffect(() => {
    if (state.success && state.data) {
      addToast(state.message, 'success');
      loginSuccess(state.data);

      // 온보딩 여부에 따른 리다이렉트
      if (state.data.onboardingCompleted) {
        navigate('/');
      } else {
        navigate('/onboarding');
      }
    } else if (state.message && !state.success) {
      addToast(state.message, 'error');
    }
  }, [state, navigate, addToast, loginSuccess]);

  return (
    <form action={formAction} className="flex flex-col gap-4">
      <Input
        label="이메일"
        name="email"
        type="email"
        placeholder="example@test.com"
        required
      />
      {state.errors.email && <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.email}</p>}

      <Input
        label="비밀번호"
        name="password"
        type="password"
        placeholder="비밀번호를 입력하세요"
        required
      />
      {state.errors.password && <p className="text-error-red text-[13px] ml-1 font-medium">{state.errors.password}</p>}

      <Button type="submit" className="mt-8" disabled={isPending}>
        {isPending ? '로그인 중...' : '로그인'}
      </Button>
    </form>
  );
};
