import { useNavigate } from 'react-router-dom';

interface Card {
  id: string;
  name: string;
  number: string;
  type: 'CREDIT' | 'CHECK';
  company: string;
}

const DUMMY_CARDS: Card[] = [
  {
    id: '1',
    name: '신한 Deep Dream',
    number: '1234-****-****-5678',
    type: 'CREDIT',
    company: '신한카드',
  },
  {
    id: '2',
    name: 'KB국민 노리 체크카드',
    number: '8765-****-****-4321',
    type: 'CHECK',
    company: 'KB국민카드',
  },
  {
    id: '3',
    name: '현대카드 ZERO Edition2',
    number: '4321-****-****-8765',
    type: 'CREDIT',
    company: '현대카드',
  },
];

export const CardListPage = () => {
  const navigate = useNavigate();

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5">
        <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">내 카드 목록</h1>
        <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
          보유하고 계신 카드 목록과 결제 내역을 확인해보세요.
        </p>
      </div>

      <div className="mx-7 border-t border-gray-100" />

      <div className="px-7 py-6 flex-1 flex flex-col gap-4">
        {DUMMY_CARDS.map((card) => (
          <div
            key={card.id}
            onClick={() => navigate(`/finance/cards/${card.id}`)}
            className="flex items-center justify-between p-5 rounded-2xl border border-gray-100 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer group bg-gradient-to-br from-white to-gray-50/50 hover:to-blue-50/10"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center shrink-0 group-hover:bg-blue-50 transition-colors">
                <svg
                  className="w-6 h-6 text-gray-400 group-hover:text-blue-500 transition-colors"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                  />
                </svg>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[15px] font-bold text-gray-800">{card.name}</span>
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                      card.type === 'CREDIT'
                        ? 'bg-blue-50 text-blue-600'
                        : 'bg-emerald-50 text-emerald-600'
                    }`}
                  >
                    {card.type === 'CREDIT' ? '신용' : '체크'}
                  </span>
                </div>
                <div className="text-[13px] text-gray-400 font-medium">
                  {card.company} | {card.number}
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
        ))}
      </div>
    </div>
  );
};
