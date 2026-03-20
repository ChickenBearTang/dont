import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentMonthSpending } from '../report/hooks/useReportQueries';

/**
 * 금융 카테고리 카드 컴포넌트
 */
const CategoryCard: React.FC<{
  title: string;
  description: string;
  icon: string;
  path: string;
  color: string;
  extraContent?: React.ReactNode;
}> = ({ title, description, icon, path, color, extraContent }) => {
  const navigate = useNavigate();

  return (
    <div
      onClick={() => navigate(path)}
      className="group relative overflow-hidden bg-white p-8 rounded-[32px] border border-gray-100 shadow-sm hover:shadow-xl transition-all duration-500 cursor-pointer flex flex-col justify-between min-h-[240px]"
    >
      {/* Background Accent */}
      <div
        className={`absolute top-0 right-0 w-32 h-32 -mr-8 -mt-8 rounded-full opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-500 ${color}`}
      />

      <div>
        <div
          className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl mb-6 shadow-sm group-hover:scale-110 transition-transform duration-500 ${color.replace('bg-', 'bg-opacity-10 ')}`}
        >
          {icon}
        </div>
        <h3 className="text-xl font-black text-eel mb-2 group-hover:text-primary-blue transition-colors">
          {title}
        </h3>
        <p className="text-gray text-sm font-medium leading-relaxed mb-4">{description}</p>
        {extraContent}
      </div>

      <div className="flex items-center text-gray-400 group-hover:text-primary-blue transition-colors text-sm font-bold">
        바로가기
        <svg
          className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="9 5l7 7-7 7" />
        </svg>
      </div>
    </div>
  );
};

/**
 * 금융 서비스 통합 홈 페이지
 */
export const FinanceHomePage: React.FC = () => {
  const { data: spendingData } = useCurrentMonthSpending();

  return (
    <div className="max-w-6xl mx-auto px-6 lg:px-10 py-16">
      <div className="mb-14">
        <h1 className="text-4xl lg:text-5xl font-black text-eel mb-4 tracking-tight">
          금융 <span className="text-primary-blue">홈</span>
        </h1>
        <p className="text-gray text-lg font-medium opacity-80">
          모든 금융 자산을 스마트하게 관리하고 더 나은 미래를 계획해 보세요.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10">
        {/* 좌 상단: 세이브박스 */}
        <CategoryCard
          title="세이브박스"
          description="목표 금액을 정하고 똑똑하게 돈을 모으는 전용 금고를 만드세요."
          icon="🎁"
          path="/savebox-setup"
          color="bg-amber-500"
        />

        {/* 우 상단: 내 결제내역 */}
        <CategoryCard
          title="내 결제내역"
          description="이번 달 카드 지출 현황을 실시간으로 분석해 드립니다."
          icon="📊"
          path="/finance/report"
          color="bg-emerald-500"
          extraContent={
            <div className="mt-2 bg-gray-50 p-4 rounded-2xl border border-gray-100 group-hover:border-emerald-100 transition-colors">
              <span className="text-xs font-bold text-gray-400 block mb-1">이번 달 총 지출</span>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-black text-emerald-600">
                  {spendingData?.totalAmount?.toLocaleString() || 0}
                </span>
                <span className="text-sm font-bold text-eel">원</span>
              </div>
            </div>
          }
        />

        {/* 좌 하단: 내 계좌 */}
        <CategoryCard
          title="내 계좌"
          description="연결된 모든 은행 계좌의 잔액과 거래 내역을 한눈에 관리하세요."
          icon="🏦"
          path="/account"
          color="bg-blue-500"
        />

        {/* 우 하단: 내 카드 */}
        <CategoryCard
          title="내 카드"
          description="사용 중인 카드의 결제 예정 금액과 혜택 정보를 확인하세요."
          icon="💳"
          path="/finance/cards"
          color="bg-purple-500"
        />
      </div>
    </div>
  );
};
