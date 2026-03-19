import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCard, getCardTransactions } from '../api/cardApi';
import type { CardDto, TransactionDto } from '../types';

export const CardDetailPage = () => {
  const { cardId } = useParams<{ cardId: string }>();
  const navigate = useNavigate();

  const [cardInfo, setCardInfo] = useState<CardDto | null>(null);
  const [transactions, setTransactions] = useState<TransactionDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!cardId) return;

    const fetchDetail = async () => {
      try {
        setLoading(true);
        const [cardRes, txRes] = await Promise.all([getCard(cardId), getCardTransactions(cardId)]);

        const cardData = 'data' in cardRes ? cardRes.data : (cardRes as unknown as CardDto);
        const txData = 'data' in txRes ? txRes.data : (txRes as unknown as TransactionDto[]);

        setCardInfo(cardData || null);
        setTransactions(Array.isArray(txData) ? txData : []);
      } catch (error) {
        console.error('Failed to fetch card details:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [cardId]);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('ko-KR', {
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-gray-100 border-t-blue-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!cardInfo) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <h2 className="text-lg font-bold text-gray-800">카드를 찾을 수 없습니다.</h2>
        <button
          onClick={() => navigate('/finance/cards')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px]">
      <div className="px-7 pt-7 pb-5 flex items-center justify-between border-b border-gray-100">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/finance/cards')}
            className="p-2 -ml-2 text-gray-400 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-[20px] font-bold text-gray-900 tracking-[-0.02em]">
              {cardInfo.cardName}
            </h1>
            <p className="text-gray-400 mt-1 text-[13px] font-medium tracking-[-0.01em]">
              {cardInfo.cardIssuerName} | 이번 달 ₩{cardInfo.monthlyCardExpense.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      <div className="px-7 py-6 flex-1 flex flex-col">
        <h2 className="text-[16px] font-bold text-gray-800 mb-4 tracking-tight">결제 내역</h2>

        {transactions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 rounded-xl bg-gray-50 flex items-center justify-center mb-3">
              <svg
                className="w-6 h-6 text-gray-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
                />
              </svg>
            </div>
            <p className="font-semibold text-gray-400 text-[13px]">결제 내역이 없습니다</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between py-4 border-b border-gray-50 hover:bg-gray-50/50 transition-colors px-4 -mx-4 rounded-xl"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                    <span className="text-[12px] font-bold text-blue-600">{tx.category[0]}</span>
                  </div>
                  <div>
                    <div className="text-[15px] font-bold text-gray-800 mb-0.5">{tx.merchant}</div>
                    <div className="text-[12px] text-gray-400 font-medium">
                      {formatDate(tx.date)} | {tx.category}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`text-[16px] font-bold tracking-tight ${tx.type === 'REFUND' ? 'text-emerald-500' : 'text-gray-900'}`}
                  >
                    {tx.type === 'REFUND' ? '+' : '-'}
                    {Math.abs(tx.amount).toLocaleString()}원
                  </div>
                  <div className="text-[11px] font-bold text-gray-300 mt-1">
                    {tx.type === 'REFUND' ? '결제 취소' : '일시불'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
