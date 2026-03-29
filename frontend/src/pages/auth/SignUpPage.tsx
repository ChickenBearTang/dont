import { useNavigate } from 'react-router-dom';
import { SignUpForm } from '@/features/auth/components/SignUpForm';


const SignUpPage = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-[600px] mx-auto py-10">
      {}
      <div className="text-center mb-10">
        <h2 className="text-3xl font-black text-gray-900 tracking-tight leading-tight">
          똑똑한 자산 관리의 시작,
          <br />
          <span className="text-primary-blue text-4xl">회원가입</span>
        </h2>
        <p className="text-gray-500 mt-3 font-medium italic">
          "돈트와 함께라면 불필요한 지출이 사라집니다."
        </p>
      </div>

      <div className="bg-[#F8FAFC] p-8 lg:p-12 rounded-[40px] shadow-sm border border-gray-100 relative overflow-hidden">
        {}
        <div className="absolute top-0 right-0 w-32 h-32 opacity-10 pointer-events-none">
          <img
            src="/assets/mascot_happy.png"
            alt=""
            className="w-full h-full object-contain rotate-12"
          />
        </div>

        <div className="mb-10 flex items-start gap-4 bg-white p-5 rounded-3xl border border-gray-50 shadow-sm">
          <div className="w-12 h-12 flex-shrink-0 bg-primary-blue/10 rounded-2xl flex items-center justify-center">
            <span className="text-2xl">🎁</span>
          </div>
          <p className="text-[14px] font-bold text-gray-700 leading-relaxed break-keep">
            환영합니다! 가입을 위해 기수 정보와 목표 금액 등 몇 가지 정보만 알려주세요. 현명한 지출
            관리를 위한 맞춤형 리포트를 준비해드릴게요.
          </p>
        </div>

        <SignUpForm />

        <div className="mt-10 pt-8 border-t border-gray-200 text-center font-semibold text-[14px]">
          <span className="text-gray-500">이미 돈트 회원이신가요?</span>{' '}
          <button
            onClick={() => navigate('/login')}
            className="text-primary-blue hover:underline underline-offset-8 transition-all"
          >
            로그인하러 가기
          </button>
        </div>
      </div>
    </div>
  );
};

export default SignUpPage;
