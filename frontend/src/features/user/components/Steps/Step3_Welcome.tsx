import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';

export const Step3_Welcome = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center text-center animate-in fade-in zoom-in duration-700">
      <div className="relative mb-12">
        <div className="absolute inset-0 bg-primary-blue/20 blur-3xl rounded-full scale-150 animate-pulse" />
        <Mascot
          src="/assets/mascot_happy.png"
          speech="축하합니다! 모든 준비가 끝났어요. 이제 돈트와 함께 똑똑한 저축 습관을 만들어봐요!"
          className="relative z-10"
        />
      </div>

      <div className="space-y-4 mb-12">
        <h2 className="text-3xl font-black text-gray-900">환영합니다! 🎊</h2>
        <p className="text-gray-500 font-medium">
          설정하신 목표를 달성할 수 있도록
          <br />
          매일매일 지출 리포트를 배달해드릴게요.
        </p>
      </div>

      <Button onClick={() => navigate('/finance-connect')} className="max-w-[300px]">
        계좌 연동으로 이동
      </Button>
    </div>
  );
};
