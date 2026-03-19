import { useEffect, useState } from 'react';
import { getSpendingSummary } from '../api/reportApi';
import type { SpendingSummaryResponse, SpendingSummaryRank } from '../types';

const CATEGORY_COLORS = [
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#F59E0B', // Amber
  '#EC4899', // Pink
  '#10B981', // Emerald
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#F43F5E', // Rose
  '#84CC16', // Lime
  '#06B6D4', // Cyan
  '#9CA3AF', // Gray (fallback)
];

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
  const lastDay = new Date(year, month + 1, 0);
  return {
    startDate: formatToYYYYMMDD(firstDay),
    endDate: formatToYYYYMMDD(lastDay),
  };
};

const DonutChart = ({ data }: { data: SpendingSummaryRank[] }) => {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  let strokeDashoffset = 0;

  return (
    <div className="relative w-52 h-52 mx-auto filter drop-shadow hover:drop-shadow-md transition-all">
      <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
        {data.length === 0 ? (
          <circle cx="50" cy="50" r={radius} fill="transparent" stroke="#F3F4F6" strokeWidth="16" />
        ) : (
          data.map((slice, i) => {
            const p = slice.percentage > 1 ? slice.percentage / 100 : slice.percentage;
            const sliceLength = p * circumference;
            const offset = strokeDashoffset;
            strokeDashoffset += sliceLength;
            return (
              <circle
                key={i}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={CATEGORY_COLORS[i % CATEGORY_COLORS.length]}
                strokeWidth="16"
                strokeDasharray={`${sliceLength} ${circumference}`}
                strokeDashoffset={-offset}
                className="transition-all duration-1000 ease-out hover:opacity-80 cursor-pointer hover:stroke-[18px]"
              />
            );
          })
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-[13px] font-bold text-gray-400">이달의 지출</span>
      </div>
    </div>
  );
};

export const MonthlyReportPage = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [summary, setSummary] = useState<SpendingSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        const { startDate, endDate } = getMonthRange(currentDate);
        const res = await getSpendingSummary(startDate, endDate);

        let rankList = res.rankColumList || [];
        rankList = [...rankList].sort((a, b) => b.percentage - a.percentage);

        setSummary({
          ...res,
          rankColumList: rankList,
        });
      } catch (error) {
        console.error('Failed to fetch spending summary:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [currentDate]);

  const handlePrevMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  return (
    <div className="w-full max-w-3xl mx-auto bg-gray-50/30 rounded-2xl overflow-hidden flex flex-col min-h-[600px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <div className="bg-white px-7 pt-7 pb-5">
        <h1 className="text-[22px] font-bold text-gray-900 tracking-[-0.02em]">
          이달의 소비 리포트
        </h1>
        <p className="text-[13px] font-medium text-gray-400 mt-1">
          회원님의 카테고리별 주요 소비패턴을 분석합니다.
        </p>
      </div>

      <div className="flex-1 p-7 flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8 bg-white p-2.5 rounded-2xl shadow-sm border border-gray-100/80">
          <button
            onClick={handlePrevMonth}
            className="p-2.5 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-800 transition"
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
          <div className="text-center font-black text-gray-800 text-[17px] tracking-tight">
            {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
          </div>
          <button
            onClick={handleNextMonth}
            disabled={
              currentDate.getMonth() === new Date().getMonth() &&
              currentDate.getFullYear() === new Date().getFullYear()
            }
            className="p-2.5 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-800 transition disabled:opacity-20 disabled:hover:bg-transparent"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-20">
            <div className="w-8 h-8 border-4 border-gray-100 border-t-blue-600 rounded-full animate-spin mb-4" />
            <span className="text-[13px] font-semibold">리포트를 분석 중입니다...</span>
          </div>
        ) : summary ? (
          <div className="flex flex-col gap-6">
            <div className="bg-white rounded-3xl p-7 border border-gray-100 shadow-sm flex flex-col items-center">
              <h3 className="text-[16px] font-extrabold text-gray-900 mb-8 w-full text-center">
                전체 소비 요약
              </h3>

              <DonutChart data={summary.rankColumList} />

              <div className="mt-8 text-center flex flex-col items-center">
                <p className="text-[14px] text-gray-400 font-bold mb-1 tracking-tight">
                  총 이용 금액
                </p>
                <div className="flex items-baseline justify-center">
                  <span className="text-[34px] font-black tracking-tighter text-blue-600">
                    {summary.totalAmount?.toLocaleString() || 0}
                  </span>
                  <span className="text-[18px] font-bold text-gray-800 ml-1">원</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-3xl p-7 border border-gray-100 shadow-sm">
              <h3 className="text-[16px] font-extrabold text-gray-900 mb-5">
                어디에 가장 많이 썼을까요?
              </h3>
              {summary.rankColumList.length === 0 ? (
                <div className="py-12 text-center text-[14px] font-bold text-gray-400 bg-gray-50 rounded-2xl">
                  해당 월의 결제 내역이 없습니다.
                </div>
              ) : (
                <div className="flex flex-col gap-3">
                  {summary.rankColumList.map((rank, idx) => {
                    const p = rank.percentage > 1 ? rank.percentage / 100 : rank.percentage;
                    const displayPercent = (p * 100).toFixed(1);

                    return (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-5 bg-white border border-gray-100 rounded-2xl hover:border-blue-100 hover:shadow-sm transition-all group cursor-pointer"
                      >
                        <div className="flex items-center gap-4">
                          <div
                            className="w-12 h-12 rounded-full flex items-center justify-center shrink-0 shadow-inner"
                            style={{
                              backgroundColor: `${CATEGORY_COLORS[idx % CATEGORY_COLORS.length]}15`,
                            }}
                          >
                            <span
                              className="text-[15px] font-black group-hover:scale-110 transition-transform"
                              style={{ color: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                            >
                              {idx + 1}위
                            </span>
                          </div>
                          <div>
                            <div className="text-[16px] font-extrabold text-gray-800 mb-0.5">
                              {rank.categoryName}
                            </div>
                            <div className="text-[12px] font-bold text-gray-400">
                              전체 지출의 {displayPercent}% 차지
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-[18px] font-black tracking-tight text-gray-900 group-hover:text-blue-600 transition-colors">
                            {rank.amount?.toLocaleString() || 0}원
                          </div>
                          {rank.amount_prv > 0 && (
                            <div className="text-[12px] font-semibold text-gray-400 mt-1">
                              저번 달보다 {((rank.amount / rank.amount_prv) * 100).toFixed(0)}%
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            데이터를 불러올 수 없습니다.
          </div>
        )}
      </div>
    </div>
  );
};
