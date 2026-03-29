import { Card } from '@/shared/components';
import { useEffect } from 'react';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import {
  useGetMyAccounts,
  useGetSavingsSetting,
} from '@/features/finance/account/hooks/useAccountQueries';
import { useCurrentMonthSpending } from '@/features/finance/report/hooks/useReportQueries';
import { fetchMyPage } from '@/features/user/api/userApi';
import { useQuery } from '@tanstack/react-query';
import { useRankingSse } from '@/features/ranking/hooks/useRankingSse';

const CATEGORY_COLORS = ['#3B82F6', '#8B5CF6', '#F59E0B', '#EC4899', '#10B981'];

const ExpenditureCard = () => {
  const now = new Date();
  const monthLabel = `${now.getFullYear()}년 ${now.getMonth() + 1}월`;
  const { data, isLoading, isError } = useCurrentMonthSpending();


  const totalAmount: number =
    (data as { data?: { totalAmount?: number }; totalAmount?: number } | undefined)?.data
      ?.totalAmount ??
    (data as { totalAmount?: number } | undefined)?.totalAmount ??
    0;

  const rankList: { categoryName: string; amount: number; percentage: number }[] =
    (
      data as
      | {
        data?: {
          rankColumList?: { categoryName: string; amount: number; percentage: number }[];
        };
        rankColumList?: { categoryName: string; amount: number; percentage: number }[];
      }
      | undefined
    )?.data?.rankColumList ??
    (
      data as
      | { rankColumList?: { categoryName: string; amount: number; percentage: number }[] }
      | undefined
    )?.rankColumList ??
    [];

  const top3 = [...rankList].sort((a, b) => b.amount - a.amount).slice(0, 3);

  return (
    <Card className="p-8 flex flex-col h-full">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-eel font-black text-[20px] tracking-tight flex items-center gap-2">
          <span>💸</span> 이번 달 지출 현황
        </h3>
        <span className="text-[13px] font-bold text-primary-blue bg-primary-blue/10 px-3 py-1 rounded-full">
          {monthLabel}
        </span>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-surface-soft border-t-primary-blue rounded-full animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex-1 flex items-center justify-center text-text-muted text-[14px] font-bold bg-surface-soft/50 rounded-2xl">
          데이터를 불러올 수 없습니다.
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          {}
          <div className="flex flex-col items-center justify-center py-6 bg-gradient-to-b from-surface-soft/40 to-transparent rounded-[24px] border border-line-soft shadow-inner mb-6">
            <p className="text-[13px] font-bold text-text-muted mb-2">이번 달 총 지출액</p>
            <div className="flex items-baseline gap-1.5">
              <span className="text-[2.5rem] font-black tracking-tighter text-primary-blue leading-none">
                {totalAmount.toLocaleString()}
              </span>
              <span className="text-[1.25rem] font-bold text-eel">원</span>
            </div>
          </div>

          {}
          <div className="flex-1 flex flex-col justify-end">
            <h4 className="text-[14px] font-extrabold text-eel mb-3">많이 쓴 카테고리 TOP 3</h4>
            {top3.length > 0 ? (
              <div className="flex flex-col gap-2.5">
                {top3.map((item, idx) => {
                  const pct = item.percentage > 1 ? item.percentage : item.percentage * 100;
                  return (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-3.5 bg-white rounded-2xl border border-line-soft shadow-sm hover:border-primary-blue/30 hover:shadow-md transition-all group"
                    >
                      <div
                        className="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-white text-[13px] font-black shadow-inner group-hover:scale-105 transition-transform"
                        style={{ backgroundColor: CATEGORY_COLORS[idx] }}
                      >
                        {idx + 1}위
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-[14px] font-bold text-eel truncate mb-0.5">
                          {item.categoryName}
                        </div>
                        <div className="text-[11px] font-bold text-text-muted">
                          전체 지출의 {pct.toFixed(1)}%
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-[15px] font-black tracking-tight text-eel">
                          {item.amount.toLocaleString()}원
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center p-6 bg-surface-soft/30 rounded-2xl border border-line-soft border-dashed">
                <p className="text-center text-[13px] font-bold text-text-muted">
                  이번 달 지출 내역이 없어요!
                  <br />
                  아주 훌륭합니다 👍
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

export const DashboardPage = () => {
  const { user, updateUser } = useAuthStore();
  const { data: accounts, isLoading: isLoadingAccounts } = useGetMyAccounts();
  const { data: setting, isLoading: isLoadingSetting } = useGetSavingsSetting();
  useRankingSse();

  const { data: profile } = useQuery({
    queryKey: ['myPage'],
    queryFn: () => fetchMyPage().then((res) => res.data),
    staleTime: 1000 * 60 * 30,
  });


  useEffect(() => {
    if (profile?.nickname && user?.nickname !== profile.nickname) {
      updateUser({ nickname: profile.nickname });
    }
  }, [profile?.nickname, user?.nickname, updateUser]);

  const displayNickname = profile?.nickname || user?.nickname || '회원';

  const savebox =
    accounts?.find((a) => a.id === setting?.saveboxAccountId) ||
    accounts?.find(
      (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
    );

  const isLoadingSavebox = isLoadingAccounts || isLoadingSetting;
  const balance = savebox ? Number(savebox.accountBalance) : 0;

  return (
    <div className="space-y-10 max-w-[1400px] mx-auto w-full pt-4 lg:pt-6 xl:pt-8 pb-20 px-4">
      {}
      <div className="relative glass-premium rounded-[48px] p-8 lg:p-12 xl:p-14 flex flex-col xl:flex-row items-center justify-between gap-10 overflow-hidden transition-all duration-500 hover:shadow-[0_20px_60px_rgba(31,38,135,0.12)] group">
        {}
        <div className="absolute top-[-10%] right-[-5%] w-[400px] h-[400px] bg-primary-blue/15 rounded-full blur-[100px] pointer-events-none group-hover:scale-110 transition-transform duration-1000"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[300px] h-[300px] bg-accent/15 rounded-full blur-[80px] pointer-events-none group-hover:scale-110 transition-transform duration-1000 delay-150"></div>

        {}
        <div className="absolute inset-0 bg-pattern-dots opacity-[0.4] pointer-events-none mix-blend-overlay"></div>

        {}
        <div className="flex-1 min-w-0 relative z-10 text-left">
          <h2 className="text-[2.25rem] lg:text-[2.75rem] xl:text-[3.25rem] font-black text-eel leading-[1.2] tracking-tighter">
            안녕하세요,{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-blue via-indigo-500 to-accent animate-gradient-x">
              {displayNickname}
            </span>
            님!
            <br />
            오늘도 현명한 소비 중이시네요.
          </h2>
          <p className="text-text-muted font-bold text-[1.1rem] mt-6 opacity-80">
            "작은 아낌이 모여 당신의 큰 꿈을 만듭니다."
          </p>
        </div>

        {}
        <div className="shrink-0 w-full max-w-[450px] xl:w-[500px] relative z-10 mt-4 xl:mt-0">
          <div className="flex flex-col items-center text-center bg-white/60 backdrop-blur-md px-10 py-10 rounded-[36px] border border-white/40 shadow-[0_15px_45px_rgba(15,23,42,0.08)] hover:border-primary-blue/40 transition-all duration-300">
            <div className="flex items-center gap-3 mb-6">
              <span className="text-[1rem] font-black tracking-tight text-text-muted">
                현재 세이브박스 잔액
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[3rem] lg:text-[3.5rem] xl:text-[4rem] font-black tracking-tighter text-primary-blue leading-none">
                {isLoadingSavebox ? '...' : balance.toLocaleString()}
              </span>
              <span className="text-[1.5rem] font-bold text-eel">원</span>
            </div>
          </div>
        </div>
      </div>

      {}
      <div className="grid lg:grid-cols-3 gap-10 xl:gap-12 relative z-10">
        {}
        <div className="lg:col-span-1 glass-premium hover-glass rounded-[40px] overflow-hidden">
          <ExpenditureCard />
        </div>

        {}
        <div className="lg:col-span-1 glass-premium hover-glass rounded-[40px] overflow-hidden">
          <RankingWidget />
        </div>

        {}
        <div className="lg:col-span-1 glass-premium hover-glass rounded-[40px] overflow-hidden">
          <PollWidget />
        </div>
      </div>
    </div>
  );
};


import axiosInstance from '@/shared/api/axiosInstance';
import { getPosts } from '@/features/community/api/communityApi';
import { useNavigate } from 'react-router-dom';

interface RankingUser {
  userId: number;
  nickname: string | null;
  rank: number;
  score: number;
}

const RankingWidget = () => {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard', 'ranking'],
    queryFn: async () => {
      const res = await axiosInstance.get('/ranking/cohort');
      return res.data;
    },
  });

  const myRanking = data?.myRanking;
  const top3 = data?.top100?.slice(0, 3) || [];

  return (
    <Card className="p-8 flex flex-col h-full border border-indigo-50 shadow-sm relative overflow-hidden group">
      {}
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-100 rounded-full blur-[60px] opacity-60 -mr-10 -mt-10 pointer-events-none" />

      <div className="flex items-center justify-between mb-6 relative z-10">
        <h3 className="text-eel font-black text-[18px] tracking-tight flex items-center gap-2">
          <span>🏆</span> 우리 기수 랭킹
        </h3>
        <button
          onClick={() => navigate('/ranking')}
          className="text-[12px] font-bold text-indigo-500 bg-indigo-50 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors"
        >
          전체보기
        </button>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-indigo-100 border-t-indigo-500 rounded-full animate-spin" />
        </div>
      ) : isError ? (
        <div className="flex-1 flex items-center justify-center text-text-muted text-[13px] font-bold">
          랭킹 정보를 불러오지 못했습니다.
        </div>
      ) : (
        <div className="flex-1 flex flex-col justify-between relative z-10">
          {}
          <div className="flex flex-col items-center justify-center py-5 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl shadow-md mb-5 text-white">
            <p className="text-[12px] font-bold text-indigo-100 mb-1">내 현재 순위</p>
            {myRanking && myRanking.rank !== -1 ? (
              <div className="flex items-baseline gap-1">
                <span className="text-[2rem] font-black tracking-tighter leading-none">
                  {myRanking.rank}
                </span>
                <span className="text-[1rem] font-bold text-indigo-100">위</span>
              </div>
            ) : (
              <p className="text-[14px] font-bold mt-1">랭킹 산정 중</p>
            )}
          </div>

          {}
          <div className="flex-1 flex flex-col justify-end gap-2">
            {top3.length > 0 ? (
              top3.map((user: RankingUser) => (
                <div
                  key={user.userId}
                  className="flex items-center justify-between p-3 bg-white border border-line-soft rounded-xl shadow-sm"
                >
                  <div className="flex items-center gap-3 w-full">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${user.rank === 1
                        ? 'bg-yellow-100 text-yellow-700'
                        : user.rank === 2
                          ? 'bg-slate-100 text-slate-600'
                          : 'bg-orange-50 text-orange-600'
                        }`}
                    >
                      {user.rank}
                    </span>
                    <span className="text-[13px] font-bold text-eel truncate max-w-[100px]">
                      {user.nickname || `유저 ${user.userId}`}
                    </span>
                    <span className="ml-auto text-[13px] font-black text-indigo-600 shrink-0">
                      {user.score.toLocaleString()}원
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-[13px] text-text-muted font-bold py-4">
                기수에 등록된 랭커가 없습니다.
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
};

const PollWidget = () => {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboard', 'poll'],
    queryFn: async () => {
      const res = await getPosts('POLL', undefined, 0, 1);
      return res.data;
    },
  });

  const pollPost = data?.content?.[0];
  const pollInfo = pollPost?.extraSummary?.poll;

  return (
    <Card className="p-8 flex flex-col h-full border border-amber-50 shadow-sm relative overflow-hidden group">
      {}
      <div className="absolute top-0 right-0 w-32 h-32 bg-amber-100 rounded-full blur-[60px] opacity-50 -mr-10 -mt-10 pointer-events-none" />

      <div className="flex items-center justify-between mb-6 relative z-10">
        <h3 className="text-eel font-black text-[18px] tracking-tight flex items-center gap-2">
          <span>🔥</span> 핫한 절약 논쟁
        </h3>
        <button
          onClick={() => navigate('/community?category=POLL')}
          className="text-[12px] font-bold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full hover:bg-amber-100 transition-colors"
        >
          투표하기
        </button>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-4 border-amber-100 border-t-amber-500 rounded-full animate-spin" />
        </div>
      ) : isError || !pollPost || !pollInfo ? (
        <div className="flex-1 flex items-center justify-center text-text-muted text-[13px] font-bold bg-surface-soft/50 rounded-2xl">
          진행 중인 토론이 없습니다.
        </div>
      ) : (
        <div
          onClick={() => navigate(`/community/${pollPost.postId}`)}
          className="flex-1 flex flex-col justify-between relative z-10 cursor-pointer group/card"
        >
          {}
          <div className="bg-white p-5 rounded-2xl border border-line-soft shadow-sm mb-4 group-hover/card:border-amber-300 transition-colors">
            <h4 className="text-[15px] font-extrabold text-eel mb-2 leading-snug line-clamp-2 gap-1.5 flex">
              <span className="text-amber-500 shrink-0">Q.</span>
              <span>{pollInfo.question || pollPost.title}</span>
            </h4>
            <div className="flex items-center gap-2 text-[11px] font-bold text-text-muted mt-3">
              <span className="bg-surface-soft px-2 py-1 rounded-md">
                {pollPost.authorNickname}
              </span>
              <span>참여자 {pollInfo.totalVoteCount?.toLocaleString() || 0}명</span>
            </div>
          </div>

          {}
          <div className="flex flex-col gap-2 mt-auto">
            <div className="flex items-center justify-between p-3.5 bg-gray-50 rounded-xl border border-gray-100 relative overflow-hidden">
              <div
                className="absolute left-0 top-0 bottom-0 bg-blue-100 opacity-40 transition-all duration-1000"
                style={{
                  width: `${pollInfo.totalVoteCount > 0 ? (pollInfo.optionACount / pollInfo.totalVoteCount) * 100 : 50}%`,
                }}
              />
              <span className="text-[13px] font-bold text-eel z-10 relative truncate max-w-[70%]">
                A. {pollInfo.optionA}
              </span>
              <span className="text-[12px] font-black text-blue-600 z-10 relative">
                {pollInfo.totalVoteCount > 0
                  ? Math.round((pollInfo.optionACount / pollInfo.totalVoteCount) * 100)
                  : 0}
                %
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 bg-gray-50 rounded-xl border border-gray-100 relative overflow-hidden">
              <div
                className="absolute left-0 top-0 bottom-0 bg-red-100 opacity-40 transition-all duration-1000"
                style={{
                  width: `${pollInfo.totalVoteCount > 0 ? (pollInfo.optionBCount / pollInfo.totalVoteCount) * 100 : 50}%`,
                }}
              />
              <span className="text-[13px] font-bold text-eel z-10 relative truncate max-w-[70%]">
                B. {pollInfo.optionB}
              </span>
              <span className="text-[12px] font-black text-red-500 z-10 relative">
                {pollInfo.totalVoteCount > 0
                  ? Math.round((pollInfo.optionBCount / pollInfo.totalVoteCount) * 100)
                  : 0}
                %
              </span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
