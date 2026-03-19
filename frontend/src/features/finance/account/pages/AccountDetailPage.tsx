import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGetAccountDetail, useGetAccountTransactions } from '../hooks/useAccountQueries';

/**
 * 특정 계좌의 상세 정보 및 거래 내역을 조회하는 페이지
 */
export const AccountDetailPage: React.FC = () => {
  const { accountId } = useParams<{ accountId: string }>();
  const navigate = useNavigate();
  const id = Number(accountId);

  // 현재 날짜 기준 한 달 전~오늘까지의 거래 내역 조회 (더미 파라미터)
  const today = new Date().toISOString().split('T')[0];
  const lastMonth = new Date(new Date().setMonth(new Date().getMonth() - 1))
    .toISOString()
    .split('T')[0];

  const { data: account, isLoading: isAccountLoading } = useGetAccountDetail(id);
  const { data: transactions, isLoading: isTxLoading } = useGetAccountTransactions(id, {
    startDate: lastMonth,
    endDate: today,
  });

  if (isAccountLoading || isTxLoading) {
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
      {/* 뒤로가기 버튼 */}
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

      {/* 계좌 요약 헤더 */}
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

      {/* 거래 내역 리스트 */}
      <section className="bg-white border border-light-gray rounded-3xl shadow-sm overflow-hidden">
        <div className="px-8 py-5 border-b border-light-gray flex justify-between items-center bg-gray/5">
          <h3 className="font-black text-eel">거래 내역</h3>
          <span className="text-xs text-gray">
            {lastMonth} ~ {today}
          </span>
        </div>

        <div className="divide-y divide-light-gray">
          {!transactions || transactions.length === 0 ? (
            <div className="p-16 text-center text-gray">최근 거래 내역이 없습니다.</div>
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
