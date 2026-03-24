import { useNavigate } from 'react-router-dom';
import PigImage from '@/assets/404-pig.png';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4 text-center">
      <img
        src={PigImage}
        alt="Shocked Piggy Bank with empty safe"
        className="w-64 md:w-96 h-auto object-contain mb-8 drop-shadow-2xl"
      />
      <h1 className="text-5xl md:text-6xl font-black text-gray-800 mb-3 tracking-tighter">404</h1>
      <h2 className="text-xl md:text-2xl font-bold text-gray-700 mb-4">앗, 여긴 비어있어요 !</h2>
      <p className="text-gray-500 mb-8 max-w-md mx-auto leading-relaxed text-sm md:text-base">
        텅 빈 금고처럼... 원하시는 페이지가 이미 사라졌거나 잘못된 주소를 입력하셨습니다.
        <br className="hidden md:block" />
        다시 안전한 홈으로 돌아가볼까요?
      </p>
      <button
        onClick={() => navigate('/', { replace: true })}
        className="px-8 py-3.5 bg-[#4f46e5] hover:bg-[#4338ca] text-white font-bold rounded-2xl shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
      >
        홈으로 돌아가기
      </button>
    </div>
  );
}
