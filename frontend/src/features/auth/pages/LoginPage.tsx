import { useNavigate } from 'react-router-dom';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { Mascot } from '@/shared/components/Mascot';
import { Card } from '@/shared/components';

export const LoginPage = () => {
  const navigate = useNavigate();

  return (
    <div className="relative w-full flex-1 min-h-[calc(100vh-80px)] flex items-center justify-center p-6 lg:p-12 overflow-hidden bg-gradient-to-br from-[#F8F9FA] via-[#f4f7fb] to-[#E2E8F0]">
      {}
      <div className="absolute inset-0 bg-pattern-grid opacity-50 z-0"></div>
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute -top-[20%] -right-[10%] w-[70vw] h-[70vw] rounded-full bg-gradient-to-br from-primary-blue/5 to-transparent blur-[120px] opacity-80"></div>
        <div className="absolute -bottom-[20%] -left-[10%] w-[60vw] h-[60vw] rounded-full bg-gradient-to-tr from-accent-strong/5 to-transparent blur-[100px] opacity-80"></div>
      </div>

      <div className="relative z-10 grid lg:grid-cols-2 gap-16 lg:gap-24 items-center w-full max-w-[1100px] mx-auto">
        <div className="flex flex-col items-center lg:items-start text-center lg:text-left space-y-8">
          <div className="space-y-4 relative">
            {}
            <div className="absolute -inset-4 bg-white/40 blur-2xl z-0 rounded-[100px]"></div>

            <h2 className="relative z-10 text-[2.5rem] lg:text-[3.25rem] font-black text-eel tracking-tight leading-[1.2] drop-shadow-sm">
              돈이 보이는 습관,
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-blue to-accent">
                DON'T
              </span>
              와 함께 시작하세요
            </h2>
            <p className="relative z-10 text-lg lg:text-xl text-text-muted font-semibold tracking-tight">
              "불필요한 지출은 줄이고 목표에 가까워져요."
            </p>
          </div>

          <div className="pt-20 lg:pt-32 relative group w-full flex justify-center lg:justify-start">
            <Mascot
              src="/assets/mascot_happy.png"
              speech="만나서 반가워요! 오늘은 얼마를 아껴볼까요?"
              className="w-full max-w-[360px] transition-transform duration-700 hover:-translate-y-2 relative z-10"
            />
          </div>
        </div>

        <Card className="!p-10 lg:!p-14 w-full max-w-[480px] mx-auto lg:mx-0 relative z-10">
          <div className="mb-10">
            <h3 className="text-[1.85rem] font-black text-eel tracking-tight drop-shadow-sm">
              환영합니다!
            </h3>
            <p className="text-text-muted mt-2 font-bold text-[15px]">
              로그인하고 서비스를 이용해보세요.
            </p>
          </div>

          <div>
            <LoginForm />
          </div>

          <div className="mt-10 pt-8 border-t border-line-soft/60 text-center">
            <p className="text-[15px] text-text-muted font-bold">
              아직 계정이 없으신가요?{' '}
              <button
                onClick={() => navigate('/signup')}
                className="text-primary-blue font-black hover:text-accent-strong transition-colors ml-1 relative group inline-block"
              >
                지금 시작하기
                <span className="absolute left-0 -bottom-1 w-full h-[2px] bg-primary-blue transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-300"></span>
              </button>
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
