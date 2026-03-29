import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useGetMyAccounts,
  useGetSavingsSetting,
  useGetAccountTransactions,
} from '../hooks/useAccountQueries';
import { ManualSavingsModal } from '../components/ManualSavingsModal';
import { ManualWithdrawalModal } from '../components/ManualWithdrawalModal';
import { PrimaryAccountChangeModal } from '../components/PrimaryAccountChangeModal';


export const SaveboxDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);
  const [isPrimaryModalOpen, setIsPrimaryModalOpen] = useState(false);


  const savebox =
    accounts?.find((a) => a.id === setting?.saveboxAccountId) ||
    accounts?.find(
      (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
    );


  const primaryAccount =
    accounts?.find((a) => a.id === setting?.primaryAccountId) ||
    accounts?.find((a) => a.isPrimary);


  const now = new Date();
  const past = new Date();
  past.setDate(now.getDate() - 30);
  const formatDate = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}${m}${day}`;
  };

  const { data: allTransactions } = useGetAccountTransactions(savebox?.id || 0, {
    startDate: formatDate(past),
    endDate: formatDate(now),
  });

  const recentTransactions = React.useMemo(() => {
    if (!allTransactions) return [];
    return [...allTransactions]
      .sort((a, b) => {
        const dateA = new Date(`${a.transactionDate} ${a.transactionTime}`).getTime();
        const dateB = new Date(`${b.transactionDate} ${b.transactionTime}`).getTime();
        return dateB - dateA;
      })
      .slice(0, 3);
  }, [allTransactions]);

  if (isLoadingAccounts || isLoadingSetting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-blue-100 border-t-primary-blue rounded-full animate-spin mb-4" />
        <p className="text-gray-500 font-medium font-black">정보를 불러오고 있습니다...</p>
      </div>
    );
  }

  if (!savebox) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
        <div className="text-7xl mb-10 animate-bounce">🎁</div>
        <h2 className="text-3xl font-black text-eel mb-4 tracking-tight">
          아직 세이브박스가 없네요!
        </h2>
        <p className="text-gray-400 font-medium mb-12 text-lg">
          목표 금액을 정하고 똑똑하게 돈을 모으는
          <br />
          <span className="text-primary-blue font-black">전용 금고</span>를 먼저 만들어보세요.
        </p>
        <button
          onClick={() => navigate('/finance/savebox-setup')}
          className="px-10 py-5 bg-primary-blue text-white rounded-[24px] font-black text-lg shadow-xl shadow-blue-100 hover:scale-105 active:scale-95 transition-all"
        >
          세이브박스 개설하기
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <button
        onClick={() => navigate('/finance')}
        className="flex items-center gap-2 text-gray-400 hover:text-eel font-bold mb-8 transition-colors"
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

      <div className="mb-14 text-left">
        <h1 className="text-5xl font-black text-eel tracking-tight mb-4">
          나의 <span className="text-primary-blue">세이브박스</span>
        </h1>
        <p className="text-gray-400 text-lg font-medium opacity-80">
          티끌 모아 태산! 당신의 소중한 꿈이 차곡차곡 쌓이고 있어요.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {}
        <div className="bg-white p-12 rounded-[48px] border border-gray-100 shadow-sm flex flex-col justify-between min-h-[340px] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-blue-50 to-transparent opacity-40 rounded-bl-[120px] transition-transform group-hover:scale-110" />

          <div className="relative z-10">
            <div className="flex flex-col items-start gap-3">
              <span className="text-sm font-black text-primary-blue bg-blue-50/50 px-4 py-2 rounded-full tracking-tighter">
                세이브박스 잔액
              </span>
              <div className="flex items-center gap-2 ml-1">
                <span className="text-[11px] font-black text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md tracking-tight">
                  {savebox.bankName}
                </span>
                <span className="text-[14px] font-bold text-gray-400 font-mono tracking-tight">
                  {savebox.accountNo}
                </span>
              </div>
            </div>
            <div className="mt-10 flex items-baseline gap-2">
              <span className="text-6xl font-black text-eel tracking-tighter">
                {Number(savebox.accountBalance).toLocaleString()}
              </span>
              <span className="text-2xl font-bold text-gray-300">원</span>
            </div>
          </div>

          <div className="relative z-10 mt-10 mb-4 flex flex-col flex-1">
            <h3 className="text-[14px] font-bold text-gray-800 mb-3 ml-1 flex items-center gap-1.5 opacity-80">
              최근 이체 내역
            </h3>
            {recentTransactions.length > 0 ? (
              <div className="space-y-2.5 flex-1">
                {recentTransactions.map((tx, idx) => (
                  <div
                    key={tx.transactionUniqueNo || idx}
                    className="flex justify-between items-center bg-gray-50/60 p-4 rounded-2xl border border-gray-100/50 hover:bg-white hover:shadow-sm transition-all"
                  >
                    <div>
                      <div className="font-bold text-gray-700 text-sm tracking-tight">
                        {tx.transactionSummary}
                      </div>
                      <div className="text-[11px] text-gray-400 font-mono mt-0.5 ml-0.5">
                        {tx.transactionDate.substring(4, 6)}.{tx.transactionDate.substring(6, 8)}{' '}
                        {tx.transactionTime.substring(0, 2)}:{tx.transactionTime.substring(2, 4)}
                      </div>
                    </div>
                    <div
                      className={`font-black text-sm ${tx.transactionType === '1' ? 'text-primary-blue' : 'text-red-500'}`}
                    >
                      {tx.transactionType === '1' ? '+' : '-'}
                      {Number(tx.transactionAmount).toLocaleString()}원
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center flex-1 min-h-[180px] text-sm font-medium text-gray-400 bg-gray-50/50 rounded-3xl border border-gray-50 shadow-inner">
                최근 이체 내역이 없습니다.
              </div>
            )}
          </div>

          <div className="relative z-10 mt-auto pt-4 flex flex-col gap-3">
            <button
              onClick={() => setIsManualModalOpen(true)}
              className="w-full py-4 bg-primary-blue text-white rounded-2xl font-black text-[16px] hover:bg-blue-600 active:scale-95 transition-all shadow-xl shadow-blue-50 flex items-center justify-center gap-2 group"
            >
              <span>지금 바로 저축하기</span>
              <svg
                className="w-5 h-5 group-hover:translate-x-1 transition-transform"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={3}
                  d="M14 5l7 7-7 7"
                />
              </svg>
            </button>
            <button
              onClick={() => setIsWithdrawalModalOpen(true)}
              className="w-full py-4 bg-gray-50 text-gray-400 rounded-2xl font-bold text-[15px] hover:bg-gray-100 hover:text-eel active:scale-95 transition-all flex items-center justify-center gap-2 group"
            >
              <span className="opacity-0 group-hover:opacity-100 transition-opacity">💸</span>
              <span>잔액 꺼내기</span>
            </button>
          </div>
        </div>

        {}
        <div className="space-y-8">
          {}
          <div className="bg-white p-8 rounded-[36px] border border-gray-100 shadow-sm flex items-center justify-between group hover:border-primary-blue/20 transition-all">
            <div className="flex items-center gap-5">
              <div className="min-w-0 flex flex-col items-start gap-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-black text-amber-600 bg-amber-50/50 px-3 py-1.5 rounded-full uppercase tracking-tighter">
                    주거래 통장
                  </span>
                  <h4 className="text-[16px] font-extrabold text-eel truncate mt-0.5">
                    {primaryAccount ? primaryAccount.accountName : '연결된 계좌 없음'}
                  </h4>
                </div>
                {primaryAccount && (
                  <div className="flex items-center gap-2 ml-1">
                    <span className="text-[11px] font-black text-gray-500 bg-gray-100 px-2.5 py-1 rounded-md tracking-tight">
                      {primaryAccount.bankName}
                    </span>
                    <span className="text-[14px] font-bold text-gray-400 font-mono tracking-tight">
                      {primaryAccount.accountNo}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setIsPrimaryModalOpen(true)}
              className="px-4 py-2 bg-gray-100 text-eel rounded-xl text-[13px] font-bold hover:bg-gray-200 active:scale-95 transition-all outline-none"
            >
              변경
            </button>
          </div>

          {}
          <div className="bg-white p-10 rounded-[40px] border border-gray-100 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between mb-10">
              <span className="text-sm font-black text-gray-400 uppercase tracking-widest">
                자동저축 설정
              </span>
              <div
                className={`px-4 py-1.5 rounded-full text-[10px] font-black tracking-widest ${setting?.isActive ? 'bg-primary-green/10 text-primary-green' : 'bg-red-50 text-red-500'}`}
              >
                {setting?.isActive ? '활성화' : '비활성'}
              </div>
            </div>

            {setting ? (
              <div className="space-y-10">
                <div className="flex items-center gap-6">
                  <div className="w-16 h-16 bg-blue-50/50 rounded-[20px] flex items-center justify-center text-3xl shadow-sm border border-blue-50">
                    🔍
                  </div>
                  <div>
                    <h3 className="font-black text-2xl text-eel mb-1 break-keep">
                      <span className="text-primary-blue">'{setting.keyword}'</span> 입금 시
                    </h3>
                    <p className="text-gray-400 text-sm font-medium">
                      지정된 키워드 입금 자동 감지
                    </p>
                  </div>
                </div>

                <div className="p-8 bg-gray-50/50 rounded-[32px] border border-gray-50 flex items-center justify-between">
                  <span className="font-black text-gray-400 text-sm">매회 저축액</span>
                  <div className="flex items-baseline gap-1">
                    <span className="font-black text-3xl text-primary-blue">
                      {setting.savingsAmount.toLocaleString()}
                    </span>
                    <span className="text-sm font-bold text-eel">원</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center">
                <p className="text-gray-300 font-medium italic">아직 설정된 규칙이 없어요.</p>
              </div>
            )}

            <button
              onClick={() => navigate('/finance/savings-rule-setup')}
              className="w-full mt-8 py-4 bg-eel text-white rounded-2xl font-bold text-[16px] hover:bg-black active:scale-95 transition-all shadow-xl shadow-gray-200 flex items-center justify-center gap-2 group"
            >
              <span> {setting ? '설정하기' : '설정하기'}</span>
            </button>
          </div>
        </div>
      </div>

      {}
      {savebox && (
        <>
          <ManualSavingsModal
            isOpen={isManualModalOpen}
            onClose={() => setIsManualModalOpen(false)}
            saveboxAccountName={savebox.accountName}
            primaryAccountName={primaryAccount?.accountName}
          />
          <ManualWithdrawalModal
            isOpen={isWithdrawalModalOpen}
            onClose={() => setIsWithdrawalModalOpen(false)}
            saveboxAccountName={savebox.accountName}
            primaryAccountName={primaryAccount?.accountName}
            saveboxBalance={Number(savebox.accountBalance)}
          />
        </>
      )}

      {}
      <PrimaryAccountChangeModal
        isOpen={isPrimaryModalOpen}
        onClose={() => setIsPrimaryModalOpen(false)}
        currentPrimaryAccountId={setting?.primaryAccountId}
      />
    </div>
  );
};
