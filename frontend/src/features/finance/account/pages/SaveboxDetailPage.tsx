import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetMyAccounts, useGetSavingsSetting } from '../hooks/useAccountQueries';
import { ManualSavingsModal } from '../components/ManualSavingsModal';
import { PrimaryAccountChangeModal } from '../components/PrimaryAccountChangeModal';

/**
 * 세이브박스 상세 대시보드 페이지
 * 고감도 프리미엄 디자인 및 국문 최적화 버전
 */
export const SaveboxDetailPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);
  const [isPrimaryModalOpen, setIsPrimaryModalOpen] = useState(false);

  // Find the Savebox account based on the registered ID in settings
  const savebox =
    accounts?.find((a) => a.id === setting?.saveboxAccountId) ||
    accounts?.find(
      (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
    );

  // Find the linked primary account
  const primaryAccount = accounts?.find((a) => a.id === setting?.primaryAccountId);

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
          onClick={() => navigate('/savebox-setup')}
          className="px-10 py-5 bg-primary-blue text-white rounded-[24px] font-black text-lg shadow-xl shadow-blue-100 hover:scale-105 active:scale-95 transition-all"
        >
          세이브박스 개설하기
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <div className="mb-14 text-left">
        <h1 className="text-5xl font-black text-eel tracking-tight mb-4">
          나의 <span className="text-primary-blue">세이브박스</span> 🎁
        </h1>
        <p className="text-gray-400 text-lg font-medium opacity-80">
          티끌 모아 태산! 당신의 소중한 꿈이 차곡차곡 쌓이고 있어요.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Balance Card (금액) */}
        <div className="bg-white p-12 rounded-[48px] border border-gray-100 shadow-sm flex flex-col justify-between min-h-[340px] relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-blue-50 to-transparent opacity-40 rounded-bl-[120px] transition-transform group-hover:scale-110" />

          <div className="relative z-10">
            <span className="text-sm font-black text-primary-blue bg-blue-50/50 px-4 py-2 rounded-full uppercase tracking-tighter">
              금액
            </span>
            <div className="mt-10 flex items-baseline gap-2">
              <span className="text-6xl font-black text-eel tracking-tighter">
                {Number(savebox.accountBalance).toLocaleString()}
              </span>
              <span className="text-2xl font-bold text-gray-300">원</span>
            </div>
          </div>

          <div className="relative z-10 mt-12">
            <button
              onClick={() => setIsManualModalOpen(true)}
              className="w-full py-6 bg-eel text-white rounded-[28px] font-black text-lg hover:bg-black active:scale-95 transition-all shadow-2xl shadow-gray-200 flex items-center justify-center gap-3 group"
            >
              <span>지금 바로 저축하기</span>
              <svg
                className="w-5 h-5 group-hover:translate-x-2 transition-transform"
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
          </div>
        </div>

        {/* Right Side Cards */}
        <div className="space-y-8">
          {/* Primary Account Mini Card (주거래 통장) */}
          <div className="bg-white p-8 rounded-[36px] border border-gray-100 shadow-sm flex items-center justify-between group hover:border-primary-blue/20 transition-all">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 bg-amber-50 rounded-2xl flex items-center justify-center text-2xl group-hover:rotate-6 transition-transform">
                🏦
              </div>
              <div>
                <span className="text-[10px] font-black text-amber-600 bg-amber-50/50 px-3 py-1 rounded-full uppercase tracking-tighter mb-1 inline-block">
                  주거래 통장
                </span>
                <h4 className="text-xl font-black text-eel">
                  {primaryAccount ? primaryAccount.accountName : '연결된 계좌 없음'}
                </h4>
              </div>
            </div>
            <button
              onClick={() => setIsPrimaryModalOpen(true)}
              className="px-5 py-2.5 bg-gray-50 text-gray-400 hover:bg-primary-blue hover:text-white rounded-2xl text-xs font-black transition-all"
            >
              변경
            </button>
          </div>

          {/* Savings Rule Card (자동저축 설정) */}
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
                    <h3 className="font-black text-2xl text-eel mb-1">
                      '{setting.keyword}' 입금 시
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
              onClick={() => navigate('/savings-rule-setup')}
              className="w-full mt-10 py-5 bg-white border-2 border-primary-blue/10 text-primary-blue rounded-[24px] font-black hover:bg-primary-blue/5 active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              📊 설정하기
            </button>
          </div>
        </div>
      </div>

      {/* Manual Savings Modal */}
      {savebox && (
        <ManualSavingsModal
          isOpen={isManualModalOpen}
          onClose={() => setIsManualModalOpen(false)}
          saveboxAccountName={savebox.accountName}
          primaryAccountName={primaryAccount?.accountName}
        />
      )}

      {/* Primary Account Change Modal */}
      <PrimaryAccountChangeModal
        isOpen={isPrimaryModalOpen}
        onClose={() => setIsPrimaryModalOpen(false)}
        currentPrimaryAccountId={setting?.primaryAccountId}
      />
    </div>
  );
};
