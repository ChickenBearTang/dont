import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getCardRecommendation } from '@/features/finance/report/api/reportApi';
import type { CardRecommendationResponse } from '@/features/finance/report/types';

export const CardRecommendationRankPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState<CardRecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRanking = async () => {
      try {
        setLoading(true);
        const requestedMonth = searchParams.get('month');
        const date = new Date();
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const fallbackMonth = `${yyyy}-${mm}`;
        const monthStr = requestedMonth || fallbackMonth;

        const res = await getCardRecommendation(monthStr);
        setData(res);
      } catch (error) {
        console.error('Failed to fetch card recommendation ranking:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchRanking();
  }, [searchParams]);

  return (
    <div className="w-full max-w-[760px] mx-auto min-h-screen px-4 py-8 pb-16 bg-gray-50/30">
      <div className="flex items-center mb-8 gap-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 -ml-2 rounded-xl hover:bg-white hover:shadow-sm transition-all"
        >
          <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-[22px] font-black text-gray-900 tracking-tight flex items-center gap-2">
          <span>🏆</span> AI 맞춤 추천 카드 랭킹
        </h1>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <div className="w-10 h-10 border-4 border-gray-200 border-t-indigo-600 rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-500 font-medium text-[14px]">
            회원님의 지난달 결제 내역을 시뮬레이션 중입니다...
          </p>
        </div>
      ) : !data || !data.all_cards || data.all_cards.length === 0 ? (
        <div className="bg-white rounded-[24px] border border-gray-100 p-12 text-center shadow-sm">
          <p className="text-gray-500 font-bold">카드 추천 데이터를 가져올 수 없습니다.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          {data.all_cards.map((card, idx) => (
            <div 
              key={card.card_id} 
              className={`bg-white rounded-[24px] p-6 border ${idx === 0 ? 'border-indigo-300 ring-4 ring-indigo-50 shadow-md' : 'border-gray-100 shadow-sm'} flex flex-col sm:flex-row gap-6 relative overflow-hidden transition-all hover:border-indigo-200 hover:shadow-md cursor-pointer`}
              onClick={() => navigate(`/finance/cards/${card.card_id}`)}
              style={idx === 0 ? { backgroundImage: 'linear-gradient(to right, #fefeff, #f8f9ff)' } : {}}
            >
              {idx === 0 && (
                <div className="absolute top-0 right-0 bg-indigo-600 text-white font-bold text-[11px] px-4 py-1.5 rounded-bl-xl tracking-wider">
                  BEST
                </div>
              )}
              
              <div className="flex flex-col items-center justify-center sm:w-24 shrink-0 mt-2 sm:mt-0">
                <div className={`text-[32px] font-black ${idx === 0 ? 'text-indigo-600' : idx === 1 ? 'text-gray-600' : idx === 2 ? 'text-amber-700' : 'text-gray-400'}`}>
                  {idx + 1}
                </div>
                <div className="text-[12px] font-bold text-gray-400 mt-1">순위</div>
              </div>
              
              <div className="flex-1 flex flex-col justify-center">
                <div className="mb-1 text-[13px] font-bold text-indigo-500">{card.name}</div>
                <h3 className="text-[18px] font-extrabold text-gray-900 mb-2 tracking-tight leading-snug">
                  {card.main_text}
                </h3>
                
                <div className="flex flex-col gap-1.5 mb-4">
                  {card.sub_text?.map((txt, index) => (
                    <div key={index} className="flex gap-2 items-start text-[13px] text-gray-600 font-medium">
                      <span className="text-indigo-400 mt-0.5">•</span>
                      <span>{txt}</span>
                    </div>
                  ))}
                </div>
                
                {card.comment && (
                  <div className="bg-gray-50 rounded-xl p-3 text-[13px] text-gray-700 font-medium border border-gray-100 flex gap-2 items-start opacity-90">
                    <span className="shrink-0 text-gray-400">💡</span>
                    <span className="leading-relaxed">{card.comment}</span>
                  </div>
                )}
              </div>
              
              <div className="sm:w-40 shrink-0 flex flex-col sm:items-end justify-center pt-4 sm:pt-0 border-t sm:border-t-0 border-gray-100">
                <div className="text-[12px] font-bold text-gray-500 mb-1">예상 월 할인액</div>
                <div className="text-[26px] font-black tracking-tighter text-indigo-600 mb-0.5 whitespace-nowrap">
                  {card.estimated_savings.toLocaleString()}<span className="text-[16px] ml-1">원</span>
                </div>
                <div className="text-[12px] font-bold text-gray-400 mt-1 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-100 inline-block">
                  피킹률 {card.picking_rate}%
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
