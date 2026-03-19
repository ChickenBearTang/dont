import { useNavigate } from 'react-router-dom';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { Mascot } from '@/shared/components/Mascot';

export const LoginPage = () => {
  const navigate = useNavigate();

  return (
    <div className="grid lg:grid-cols-2 gap-12 items-center max-w-[1000px] mx-auto">
      <div className="flex flex-col items-center lg:items-start text-center lg:text-left space-y-6">
        <div className="space-y-2">
          <h2 className="text-4xl font-black text-gray-900 tracking-tight leading-tight">
            돈이 보이는 습관,
            <br />
            <span className="text-primary-blue">돈트</span>와 함께 시작하세요
          </h2>
          <p className="text-lg text-gray-500 font-medium italic">
            "불필요한 지출은 줄이고 목표에 가까워져요."
          </p>
        </div>

        <Mascot
          src="/assets/mascot_happy.png"
          speech="다시 만나서 반가워요! 오늘은 얼마를 아껴볼까요?"
          className="w-full max-w-[400px]"
        />
      </div>

      <div className="bg-[#F8FAFC] p-8 lg:p-12 rounded-[32px] shadow-sm border border-gray-100 w-full max-w-[440px] mx-auto lg:mx-0">
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-900">환영합니다, 루루</h3>
          <p className="text-gray-500 mt-1 font-medium">로그인하고 서비스를 이용해보세요.</p>
        </div>

        <LoginForm />

        <div className="mt-8 pt-8 border-t border-gray-200 text-center">
          <p className="text-[14px] text-gray-500 font-semibold">
            아직 계정이 없으신가요?{' '}
            <button
              onClick={() => navigate('/signup')}
              className="text-primary-blue font-bold hover:underline underline-offset-4"
            >
              지금 시작하기
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};
