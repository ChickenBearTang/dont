import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMyCards } from '../api/cardApi';
import type { CardDto } from '../types';

const CARD_IMAGES: Record<string, string> = {
  신한카드: new URL('../../../../assets/cards/shinhan.png', import.meta.url).href,
  KB국민카드: new URL('../../../../assets/cards/kb.png', import.meta.url).href,
  현대카드: new URL('../../../../assets/cards/hyundai.png', import.meta.url).href,
  우리카드: new URL('../../../../assets/cards/woori.png', import.meta.url).href,
  하나카드: new URL('../../../../assets/cards/hana.png', import.meta.url).href,
  삼성카드: new URL('../../../../assets/cards/samsung.png', import.meta.url).href,
  NH농협카드: new URL('../../../../assets/cards/nh.png', import.meta.url).href,
  롯데카드: new URL('../../../../assets/cards/lotte.png', import.meta.url).href,
  BC카드: new URL('../../../../assets/cards/bc.png', import.meta.url).href,
  default: new URL('../../../../assets/cards/default_card.png', import.meta.url).href,
};

const getCardImage = (cardIssuerName: string) => {
  return CARD_IMAGES[cardIssuerName] || CARD_IMAGES['default'];
};

export const CardListPage = () => {
  const navigate = useNavigate();
  const [cards, setCards] = useState<CardDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCards = async () => {
      try {
        setLoading(true);
        const res = await getMyCards();
        if (res && res.cards) {
          setCards(res.cards);
        }
      } catch (error) {
        console.error('Failed to fetch cards:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCards();
  }, []);

  return (
    <div className="w-full max-w-3xl mx-auto py-8 px-4">
      <button
        onClick={() => navigate('/finance')}
        className="flex items-center gap-2 text-gray-400 hover:text-gray-800 font-bold mb-6 transition-colors"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        금융 홈으로
      </button>

      <div className="w-full bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
        <div className="px-7 pt-7 pb-5">
          <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">내 카드 목록</h1>
          <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
            보유하고 계신 카드 목록과 결제 내역을 확인해보세요.
          </p>
        </div>

        <div className="mx-7 border-t border-gray-100" />

        <div className="px-7 py-6 flex-1 flex flex-col gap-4">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center">
              <div className="w-6 h-6 border-2 border-gray-100 border-t-gray-400 rounded-full animate-spin" />
              <span className="text-[12px] text-gray-300 mt-3 font-medium">로딩 중...</span>
            </div>
          ) : cards.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-gray-400">
              등록된 카드가 없습니다.
            </div>
          ) : (
            cards.map((card, idx) => {
              return (
                <div
                  key={card.id ?? idx}
                  onClick={() => navigate(`/finance/cards/${card.id ?? idx + 1}`)}
                  className="flex items-center justify-between p-5 rounded-2xl border border-gray-100 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer group bg-gradient-to-br from-white to-gray-50/50 hover:to-blue-50/10"
                >
                  <div className="flex items-center gap-6">
                    <div className="w-32 h-20 shrink-0 group-hover:scale-105 transition-transform flex items-center justify-center drop-shadow-md">
                      <img
                        src={getCardImage(card.cardIssuerName)}
                        alt={card.cardIssuerName}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          const target = e.currentTarget as HTMLImageElement;
                          if (target.src !== CARD_IMAGES['default']) {
                            target.src = CARD_IMAGES['default'];
                          }
                        }}
                      />
                    </div>
                    <div className="flex-1 flex flex-col justify-center py-1 min-w-0 ml-2">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-[17px] font-extrabold text-gray-800 tracking-[-0.02em] truncate group-hover:text-blue-600 transition-colors">
                          {card.cardName}
                        </h3>
                        <span className="shrink-0 text-[11px] font-bold text-gray-500 bg-gray-100/80 px-2 py-0.5 rounded-md border border-gray-200/50">
                          {card.cardIssuerName}
                        </span>
                      </div>
                      <div className="flex flex-col">
                        <span className="text-[12px] font-medium text-gray-400 mb-0.5 tracking-tight">
                          이번 달 카드 이용 금액
                        </span>
                        <div className="flex items-baseline">
                          <span className="text-[22px] font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-blue-600 to-blue-800">
                            {card.monthlyCardExpense.toLocaleString()}
                          </span>
                          <span className="text-[14px] font-bold text-blue-800 ml-1">원</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-gray-300 group-hover:text-blue-500 transition-colors">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth="2.5"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
