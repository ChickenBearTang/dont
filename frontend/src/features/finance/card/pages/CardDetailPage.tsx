import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCard, getCardTransactions } from '../api/cardApi';
import type { CardDetailDto, TransactionItemDto } from '../types';

const formatToYYYYMMDD = (date: Date) => {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
};

const getMonthRange = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0); // Last day of the month
  return {
    startDate: formatToYYYYMMDD(firstDay),
    endDate: formatToYYYYMMDD(lastDay),
  };
};

export const CardDetailPage = () => {
  const { cardId } = useParams<{ cardId: string }>();
  const navigate = useNavigate();

  const [currentDate, setCurrentDate] = useState(new Date());
  const [cardInfo, setCardInfo] = useState<CardDetailDto | null>(null);
  const [transactions, setTransactions] = useState<TransactionItemDto[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!cardId) return;

    const fetchDetail = async () => {
      try {
        setLoading(true);
        const { startDate, endDate } = getMonthRange(currentDate);

        const [cardRes, txRes] = await Promise.all([
          getCard(cardId, startDate, endDate),
          getCardTransactions(cardId, startDate, endDate),
        ]);

        const cardData = 'data' in cardRes ? cardRes.data : (cardRes as unknown as CardDetailDto);
        const txData =
          'data' in txRes
            ? (txRes.data as unknown as { transaction: TransactionItemDto[] })
            : (txRes as unknown as { transaction: TransactionItemDto[] });

        setCardInfo((cardData as CardDetailDto) || null);
        setTransactions(txData?.transaction || []);
      } catch (error) {
        console.error('Failed to fetch card details:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [cardId, currentDate]);

  const handlePrevMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  const formatTransactionDate = (dateStr: string, timeStr: string) => {
    if (!dateStr) return '';
    // Format YYYYMMDD and HHMMSS
    const year = dateStr.slice(0, 4);
    const month = dateStr.slice(4, 6);
    const day = dateStr.slice(6, 8);
    const hour = timeStr ? timeStr.slice(0, 2) : '00';
    const min = timeStr ? timeStr.slice(2, 4) : '00';

    return `${year}년 ${parseInt(month, 10)}월 ${parseInt(day, 10)}일 ${hour}:${min}`;
  };

  if (loading && !cardInfo) {
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
              {cardInfo.cardIssuerName}
            </p>
          </div>
        </div>
      </div>

      <div className="px-7 py-6 flex-1 flex flex-col">
        {/* 월 선택 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={handlePrevMonth}
            className="p-2 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="text-center">
            <h2 className="text-[18px] font-black text-gray-800 tracking-tight">
              {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월 결제내역
            </h2>
            <p className="text-[13px] font-medium text-gray-400 mt-0.5">
              총 ₩{cardInfo.monthlyCardExpense?.toLocaleString() || 0}
            </p>
          </div>
          <button
            onClick={handleNextMonth}
            disabled={
              currentDate.getMonth() === new Date().getMonth() &&
              currentDate.getFullYear() === new Date().getFullYear()
            }
            className="p-2 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-600 transition disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-gray-100 border-t-blue-600 rounded-full animate-spin mb-3" />
            <p className="font-semibold text-gray-400 text-[13px]">불러오는 중...</p>
          </div>
        ) : transactions.length === 0 ? (
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
            <p className="font-semibold text-gray-400 text-[13px]">
              해당 월의 결제 내역이 없습니다
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {transactions.map((tx, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between py-4 border-b border-gray-50 hover:bg-gray-50/50 transition-colors px-4 -mx-4 rounded-xl"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                    <span className="text-[12px] font-bold text-blue-600">
                      {tx.categoryName?.[0] || '기'}
                    </span>
                  </div>
                  <div>
                    <div className="text-[15px] font-bold text-gray-800 mb-0.5">
                      {tx.merchantName}
                    </div>
                    <div className="text-[12px] text-gray-400 font-medium">
                      {formatTransactionDate(tx.transactionDate, tx.transactionTime)} |{' '}
                      {tx.categoryName}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[16px] font-bold tracking-tight text-gray-900">
                    -{Number(tx.transactionAmount).toLocaleString()}원
                  </div>
                  <div className="text-[11px] font-bold text-gray-300 mt-1">승인</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
