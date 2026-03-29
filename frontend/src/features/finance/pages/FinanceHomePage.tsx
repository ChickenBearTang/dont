import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/shared/components';
import { useCurrentMonthSpending } from '../report/hooks/useReportQueries';
import { useGetMyAccounts, useGetSavingsSetting } from '../account/hooks/useAccountQueries';
import { ManualSavingsModal } from '../account/components/ManualSavingsModal';


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
    <Card
      onClick={() => navigate(path)}
      className="group relative !p-6 lg:!p-8 !rounded-[32px] cursor-pointer min-h-[200px] flex flex-col justify-between"
    >
      {}
      <div
        className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${color} opacity-5 rounded-bl-[80px] transition-transform group-hover:scale-110`}
      />

      <div className="relative z-10 flex flex-col h-full">
        {}
        <div className="text-3xl mb-4 inline-block drop-shadow-sm transition-transform duration-500">
          {icon}
        </div>

        <div>
          <h3 className="text-[1.3rem] font-black text-eel mb-2 tracking-tight group-hover:text-primary-blue transition-colors">
            {title}
          </h3>

          {isLoading ? (
            <div className="space-y-2 mt-2">
              <div className="h-3 w-full bg-gray-50 animate-pulse rounded" />
              <div className="h-3 w-2/3 bg-gray-50 animate-pulse rounded" />
            </div>
          ) : (
            <p className="text-gray-400 text-[13px] font-medium leading-relaxed opacity-90 max-w-[240px]">
              {description}
            </p>
          )}
        </div>

        {}
        {extraContent && <div className="mt-4">{extraContent}</div>}
      </div>
    </Card>
  );
};


export const FinanceHomePage: React.FC = () => {
  const { data: spendingData } = useCurrentMonthSpending();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();
  const [isManualModalOpen, setIsManualModalOpen] = useState(false);


  const savebox =
    accounts?.find((a) => a.id === setting?.saveboxAccountId) ||
    accounts?.find(
      (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
    );

  const isLoading = isLoadingAccounts || (isLoadingSetting && !setting);

  return (
    <div className="max-w-[1240px] mx-auto px-6 pt-4 lg:pt-6 xl:pt-10 pb-20 w-full mb-8 relative">
      {}
      <div className="absolute top-[10%] left-[-10%] w-[500px] h-[500px] bg-primary-blue/12 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[20%] right-[-10%] w-[400px] h-[400px] bg-accent/12 rounded-full blur-[100px] pointer-events-none"></div>

      {}
      <div className="mb-10 lg:mb-14 relative z-10">
        <h1 className="text-[2.5rem] lg:text-[3rem] font-black tracking-tighter mb-4">
          <span className="text-primary-blue">금융</span>
        </h1>
        <p className="text-gray-400 font-bold text-[18px] max-w-2xl leading-relaxed">
          모든 금융 자산을 스마트하게 관리하고 더 나은 미래를 계획해 보세요.
          <br/>
          <span className="text-[14px] opacity-70 mt-2 block font-medium">실시간 데이터 동기화로 자산 현황을 한눈에 파악할 수 있습니다.</span>
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10 xl:gap-12 relative z-10">
        {}
        <div className="glass-premium hover-glass rounded-[32px]">
          <CategoryCard
            title="세이브박스"
            description="목표 금액을 정하고 똑똑하게 돈을 모으는 전용 금고를 만드세요."
            icon="🎁"
            path="/finance/savebox"
            color="from-amber-400 to-amber-500"
            isLoading={isLoading}
          />
        </div>

        {}
        <div className="glass-premium hover-glass rounded-[32px]">
          <CategoryCard
            title="내 결제내역"
            description="이번 달 지출 현황을 한눈에 살펴보세요."
            icon="📊"
            path="/finance/report"
            color="from-blue-400 to-blue-500"
            isLoading={!spendingData}
          />
        </div>

        {}
        <div className="glass-premium hover-glass rounded-[32px]">
          <CategoryCard
            title="내 계좌"
            description="연결된 모든 은행 계좌의 잔액과 거래 내역을 한눈에 관리하세요."
            icon="🏦"
            path="/account"
            color="from-purple-400 to-purple-500"
            isLoading={isLoadingAccounts}
          />
        </div>

        {}
        <div className="glass-premium hover-glass rounded-[32px]">
          <CategoryCard
            title="내 카드"
            description="사용 중인 카드의 결제 예정 금액과 혜택 정보를 확인하세요."
            icon="💳"
            path="/finance/cards"
            color="from-cyan-400 to-cyan-500"
            isLoading={false}
          />
        </div>
      </div>

      {}
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
