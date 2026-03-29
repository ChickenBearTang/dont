import Pig500Image from '@/assets/500-pig.png';
import { useNavigate } from 'react-router-dom';

export default function ServerErrorPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4 text-center">
      <img
        src={Pig500Image}
        alt="Shocked Piggy Bank with empty safe"
        className="w-64 md:w-96 h-auto object-contain mb-8 drop-shadow-2xl"
      />
      <h1 className="text-5xl md:text-6xl font-black text-gray-800 mb-3 tracking-tighter">500</h1>
      <h2 className="text-xl md:text-2xl font-bold text-gray-700 mb-4">
        앗, 서버에 문제가 생겼어요 !
      </h2>
      <p className="text-gray-500 mb-8 max-w-md mx-auto leading-relaxed text-sm md:text-base">
        앗, 시스템에 잠시 과부하가 걸렸나 봐요... 🐷💥
        <br className="hidden md:block" />
        개발팀이 열심히 고치고 있으니 잠시 후 다시 시도해주세요!
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
