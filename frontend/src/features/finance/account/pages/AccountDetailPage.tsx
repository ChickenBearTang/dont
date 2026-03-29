import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetAccountDetail, useGetAccountTransactions } from '../hooks/useAccountQueries';


export const AccountDetailPage: React.FC = () => {
  const { accountId } = useParams<{ accountId: string }>();
  const navigate = useNavigate();
  const id = Number(accountId);


  const [currentDate, setCurrentDate] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });


  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const startDate = formatDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), 1));
  const endDate = formatDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0));

  const now = new Date();
  const isCurrentMonth =
    currentDate.getFullYear() === now.getFullYear() &&
    currentDate.getMonth() === now.getMonth();

  const handlePrevMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    if (!isCurrentMonth) {
      setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
    }
  };

  const { data: account, isLoading: isAccountLoading } = useGetAccountDetail(id);
  const { data: transactions, isLoading: isTxLoading } = useGetAccountTransactions(id, {
    startDate,
    endDate,
  });

  if (isAccountLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-light-gray border-t-primary-blue rounded-full animate-spin" />
      </div>
    );
  }

  if (!account) {
    return (
      <div className="p-12 text-center">
        <p className="text-gray">계좌 정보를 찾을 수 없습니다.</p>
        <button onClick={() => navigate('/account')} className="mt-4 text-primary-blue font-bold">
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 mb-6 text-gray hover:text-eel transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        <span>뒤로</span>
      </button>

      {}
      <header className="p-8 mb-8 bg-white border border-light-gray rounded-3xl shadow-sm">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-sm font-medium text-gray mb-1">{account.bankName}</h2>
            <h1 className="text-2xl font-black text-eel">{account.accountName}</h1>
            <p className="text-gray font-mono">{account.accountNo}</p>
          </div>
          <span
            className={`px-3 py-1 text-xs font-bold rounded-full ${
              account.status === 'ACTIVE'
                ? 'bg-blue-bg text-primary-blue'
                : 'bg-light-gray text-gray'
            }`}
          >
            {account.status}
          </span>
        </div>

        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-black text-eel">{account.balance.toLocaleString()}</span>
          <span className="text-xl font-bold text-eel">원</span>
        </div>
      </header>

      {}
      <section className="bg-white border border-light-gray rounded-3xl shadow-sm overflow-hidden">
        <div className="px-8 py-5 border-b border-light-gray flex justify-between items-center bg-gray/5">
          <div className="flex items-center gap-4">
            <button
              onClick={handlePrevMonth}
              className="text-gray hover:text-eel p-1 rounded-full hover:bg-light-gray transition-colors"
              aria-label="이전 달"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h3 className="font-black text-eel text-lg">{currentDate.getMonth() + 1}월 거래 내역</h3>
            <button
              onClick={handleNextMonth}
              disabled={isCurrentMonth}
              className={`p-1 rounded-full transition-colors ${
                isCurrentMonth
                  ? 'text-gray/30 cursor-not-allowed'
                  : 'text-gray hover:text-eel hover:bg-light-gray'
              }`}
              aria-label="다음 달"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <span className="text-xs text-gray font-mono">
            {startDate} ~ {endDate}
          </span>
        </div>

        <div className="divide-y divide-light-gray min-h-[200px] relative">
          {isTxLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-sm z-10">
              <div className="w-8 h-8 border-4 border-light-gray border-t-primary-blue rounded-full animate-spin" />
            </div>
          ) : !transactions || transactions.length === 0 ? (
            <div className="p-16 text-center text-gray">해당 월의 거래 내역이 없습니다.</div>
          ) : (
            transactions.map((tx) => (
              <div
                key={tx.transactionUniqueNo}
                className="px-8 py-5 hover:bg-gray/5 transition-colors"
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs text-gray">
                    {tx.transactionDate} {tx.transactionTime}
                  </span>
                  <span
                    className={`font-bold ${
                      tx.transactionType === '1' ? 'text-primary-blue' : 'text-error-red'
                    }`}
                  >
                    {tx.transactionType === '1' ? '+' : '-'}{' '}
                    {Number(tx.transactionAmount).toLocaleString()} 원
                  </span>
                </div>
                <div className="flex justify-between items-end">
                  <h4 className="font-bold text-eel">{tx.transactionSummary}</h4>
                  <span className="text-xs text-gray/60">
                    잔액 {Number(tx.afterBalance).toLocaleString()} 원
                  </span>
                </div>
                {tx.transactionMemo && (
                  <p className="mt-2 text-sm text-gray/80 italic">"{tx.transactionMemo}"</p>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
};
