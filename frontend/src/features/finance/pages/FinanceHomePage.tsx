import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentMonthSpending } from '../report/hooks/useReportQueries';
import { useGetMyAccounts, useGetSavingsSetting } from '../account/hooks/useAccountQueries';
import { ManualSavingsModal } from '../account/components/ManualSavingsModal';

/**
 * 금융 카테고리 카드 컴포넌트
 * 디자인 스크린샷 100% 반영 (미니멀 화이트 로직)
 */
const CategoryCard: React.FC<{
  title: string;
  description: string;
  icon: string;
  path: string;
  color: string;
  isLoading?: boolean;
  extraContent?: React.ReactNode;
}> = ({ title, description, icon, path, color, isLoading, extraContent }) => {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(path)}
      className="group relative bg-white p-10 rounded-[40px] border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-500 cursor-pointer overflow-hidden min-h-[300px] flex flex-col justify-start"
    >
      {/* Subtle background accent circle in top-right */}
      <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${color} opacity-5 rounded-bl-[100px] transition-transform group-hover:scale-110`} />
      
      <div className="relative z-10 flex flex-col h-full">
        {/* Icon in top-left block (NO HOVER MOTION) */}
        <div className="text-4xl mb-8 inline-block drop-shadow-sm transition-transform duration-500">
          {icon}
        </div>
        
        <h3 className="text-2xl font-black text-eel mb-3 tracking-tight group-hover:text-primary-blue transition-colors">
          {title}
        </h3>
        
        {isLoading ? (
          <div className="space-y-2 mt-2">
            <div className="h-4 w-full bg-gray-50 animate-pulse rounded" />
            <div className="h-4 w-2/3 bg-gray-50 animate-pulse rounded" />
          </div>
        ) : (
          <p className="text-gray-400 text-sm font-medium leading-relaxed opacity-90 max-w-[240px]">
            {description}
          </p>
        )}
        
        {/* Dynamic content (e.g., Spending box) */}
        {extraContent && (
          <div className="mt-6">
            {extraContent}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 금융 통합 홈 페이지
 * No-Scroll / No-Icon-Motion 최적화 버전
 */
export const FinanceHomePage: React.FC = () => {
  const { data: spendingData } = useCurrentMonthSpending();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);

  // Find the savebox account based on registered settings ID
  const savebox = accounts?.find((a) => a.id === setting?.saveboxAccountId) ||
                  accounts?.find((a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스'));

  const isLoading = isLoadingAccounts || (isLoadingSetting && !setting);

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-12 h-[calc(100vh-80px)] flex flex-col justify-center overflow-hidden">
      {/* Heading Section */}
      <div className="mb-12">
        <h1 className="text-5xl font-black tracking-tight mb-4">
          <span className="text-primary-blue">금융</span> <span className="text-eel">홈</span>
        </h1>
        <p className="text-gray-400 font-medium text-lg">
          모든 금융 자산을 스마트하게 관리하고 더 나은 미래를 계획해 보세요.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
        {/* 1. 세이브박스 */}
        <CategoryCard
          title="세이브박스"
          description="목표 금액을 정하고 똑똑하게 돈을 모으는 전용 금고를 만드세요."
          icon="🎁"
          path="/finance/savebox"
          color="from-amber-400 to-amber-500"
          isLoading={isLoading}
        />

        {/* 2. 내 결제내역 */}
        <CategoryCard
          title="내 결제내역"
          description="이번 달 카드 지출 현황을 실시간으로 분석해 드립니다."
          icon="📊"
          path="/finance/report"
          color="from-blue-400 to-blue-500"
          isLoading={!spendingData}
          extraContent={
            spendingData && (
              <div className="bg-white border border-gray-100 rounded-[24px] p-6 shadow-sm flex flex-col items-start gap-1">
                <span className="text-[10px] font-black text-eel uppercase tracking-tighter opacity-60">이번 달 총 지출</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-primary-green">
                    {spendingData.totalAmount.toLocaleString()}
                  </span>
                  <span className="text-sm font-bold text-eel">원</span>
                </div>
              </div>
            )
          }
        />

        {/* 3. 내 계좌 */}
        <CategoryCard
          title="내 계좌"
          description="연결된 모든 은행 계좌의 잔액과 거래 내역을 한눈에 관리하세요."
          icon="🏦"
          path="/account"
          color="from-purple-400 to-purple-500"
          isLoading={isLoadingAccounts}
        />

        {/* 4. 내 카드 */}
        <CategoryCard
          title="내 카드"
          description="사용 중인 카드의 결제 예정 금액과 혜택 정보를 확인하세요."
          icon="💳"
          path="/finance/cards"
          color="from-cyan-400 to-cyan-500"
          isLoading={false}
        />
      </div>

      {/* Manual Savings Modal context */}
      {savebox && (
        <ManualSavingsModal
          isOpen={isManualModalOpen}
          onClose={() => setIsManualModalOpen(false)}
          saveboxAccountName={savebox.accountName}
        />
      )}
    </div>
  );
};
