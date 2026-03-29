import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useRankingSse, type RankingUser } from '../hooks/useRankingSse';
import { useRankingStore } from '../store/useRankingStore';
import { useUIStore } from '@/shared/store/useUIStore';
import axiosInstance from '@/shared/api/axiosInstance';
import { fetchCohorts } from '@/features/user/api/userApi';
import { RankingSyncModal } from '../components/RankingSyncModal';
import type { Cohort } from '@/shared/types';
import type { MyPageResponse } from '@/features/user/mypage/types';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';


interface RankingResponse {
  status: string;
  message: string;
  data: {
    top100: RankingUser[];
    myRanking: RankingUser;
  };
}


const fetchRanking = async (
  type: 'total' | 'cohort',
  cohortNo?: number
): Promise<RankingResponse> => {
  const params = type === 'cohort' && cohortNo ? `?cohortNo=${cohortNo}` : '';
  return await axiosInstance.get(`/ranking/${type}${params}`);
};


const TrendBadge: React.FC<{ diff?: number | null }> = ({ diff }) => {
  if (diff === null) {
    return (
      <div className="flex items-center justify-center px-1.5 py-0.5 bg-gradient-to-r from-yellow-100 to-amber-100 text-amber-700 border border-yellow-300/50 rounded-md text-[9px] tracking-wide font-black shadow-[0_0_8px_rgba(250,204,21,0.4)]">
        NEW
      </div>
    );
  }

  if (diff === undefined || diff === 0) {
    return (
      <div className="flex items-center justify-center w-8 h-5 bg-slate-100 rounded-md">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
      </div>
    );
  }

  const isUp = diff > 0;
  const absDiff = Math.abs(diff);

  return (
    <div
      className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[10px] font-black shadow-sm ${
        isUp ? 'bg-rose-50 text-rose-600' : 'bg-blue-50 text-blue-600'
      }`}
    >
      <span>{isUp ? '▲' : '▼'}</span>
      <span>{absDiff}</span>
    </div>
  );
};


const ProfileAvatar: React.FC<{ url?: string; rank: number; size?: string; userId?: number }> = ({
  url,
  rank,
  size = 'w-10 h-10',
  userId,
}) => {
  const [imgError, setImgError] = useState(false);

  const ringColor =
    rank === 1
      ? 'ring-yellow-400 shadow-[0_0_15px_rgba(250,204,21,0.4)]'
      : rank === 2
        ? 'ring-slate-300'
        : rank === 3
          ? 'ring-orange-300'
          : 'ring-[var(--line-soft)]';

  return (
    <motion.div
      layoutId={userId ? `avatar-${userId}` : undefined}
      className="relative"
    >
      {rank === 1 && (
        <motion.span
          initial={{ y: -10, opacity: 0, rotate: -15 }}
          animate={{ y: -6, opacity: 1, rotate: -15 }}
          className="absolute -top-4 -left-1 text-xl z-10 drop-shadow-md"
        >
          👑
        </motion.span>
      )}
      {url && !imgError ? (
        <img
          src={url}
          alt=""
          onError={() => setImgError(true)}
          className={`${size} rounded-full object-cover ring-[3px] ${ringColor} shadow-md`}
        />
      ) : (
        <div
          className={`${size} rounded-full flex items-center justify-center ${
            rank === 1
              ? 'bg-gradient-to-br from-yellow-200 to-yellow-400 text-yellow-800'
              : rank === 2
                ? 'bg-gradient-to-br from-slate-100 to-slate-300 text-slate-600'
                : rank === 3
                  ? 'bg-gradient-to-br from-orange-200 to-orange-400 text-orange-800'
                  : 'bg-[var(--surface-soft)] text-[var(--text-subtle)]'
          } ring-[3px] ${ringColor} shadow-md`}
        >
          <svg
            className={size.includes('14') || size.includes('16') ? 'w-8 h-8' : 'w-5 h-5'}
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
          </svg>
        </div>
      )}
    </motion.div>
  );
};


const Podium: React.FC<{ top3: RankingUser[] }> = ({ top3 }) => {
  const first = top3.find((u) => u.rank === 1);
  const second = top3.find((u) => u.rank === 2);
  const third = top3.find((u) => u.rank === 3);

  const PodiumSlot: React.FC<{
    user?: RankingUser;
    medal: string;
    pedestalHeight: string;
    pedestalColor: string;
    avatarSize: string;
    order: string;
    delay: number;
  }> = ({ user, medal, pedestalHeight, pedestalColor, avatarSize, order, delay }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, type: 'spring', stiffness: 40, damping: 20, mass: 2 }}
      className={`flex flex-col items-center ${order} flex-1 max-w-[220px] relative`}
    >
      <div className="flex flex-col items-center w-full">
        {user ? (
          <>
            {}
            <div className="relative mb-1">
              <span className="text-3xl drop-shadow-sm">{medal}</span>
              {}
              <div className="absolute -right-6 top-0 rotate-12 scale-90">
                <TrendBadge diff={user.rankDiff} />
              </div>
            </div>
            {}
            <div className="mb-2">
              <ProfileAvatar
                url={user.profileImageUrl}
                rank={user.rank}
                size={avatarSize}
                userId={user.userId}
              />
            </div>
            {}
            <p className="text-sm font-black text-[var(--text-strong)] text-center truncate w-full px-1 mb-0.5">
              {user.nickname || `유저 ${user.userId}`}
            </p>
            {}
            {user.cohortNo && (
              <span className="text-[10px] font-bold text-[var(--accent)] bg-[var(--accent-soft)] px-2 py-0.5 rounded-md mb-2">
                {user.cohortNo}기
              </span>
            )}
          </>
        ) : (
          <div className="mb-2 flex flex-col items-center">
            <span className="text-3xl mb-1">{medal}</span>
            <div
              className={`${avatarSize} rounded-full bg-[var(--surface-soft)] border-2 border-dashed border-[var(--line-soft)]`}
            />
            <p className="text-xs text-[var(--text-subtle)] mt-2 font-semibold">도전자 대기 중</p>
          </div>
        )}
      </div>
      <motion.div
        layout
        className={`w-full ${pedestalHeight} ${pedestalColor} rounded-t-2xl flex items-end justify-center pb-2 shadow-inner transition-transform hover:scale-[1.02]`}
      >
        <span className="text-white/90 font-black text-lg drop-shadow-md">{user?.rank ?? ''}</span>
      </motion.div>
    </motion.div>
  );

  return (
    <LayoutGroup id="ranking-container">
      <div className="mx-4 mb-6">
        <motion.div
          layout
          transition={{ type: 'spring', stiffness: 300, damping: 30, mass: 1 }}
          className="flex items-end justify-center gap-2 px-4"
        >
          {}
          <PodiumSlot
            user={second}
            medal="🥈"
            pedestalHeight="h-24"
            pedestalColor="bg-gradient-to-t from-slate-400 to-slate-200"
            avatarSize="w-20 h-20"
            order="order-1"
            delay={0.1}
          />
          {}
          <PodiumSlot
            user={first}
            medal="🥇"
            pedestalHeight="h-36"
            pedestalColor="bg-gradient-to-t from-yellow-500 to-yellow-300"
            avatarSize="w-24 h-24"
            order="order-2"
            delay={0}
          />
          {}
          <PodiumSlot
            user={third}
            medal="🥉"
            pedestalHeight="h-20"
            pedestalColor="bg-gradient-to-t from-orange-500 to-orange-300"
            avatarSize="w-20 h-20"
            order="order-3"
            delay={0.2}
          />
        </motion.div>
      </div>
    </LayoutGroup>
  );
};

export const RankingPage = () => {
  const qClient = useQueryClient();

  useRankingSse();
  const isUpdating = useRankingStore((state) => state.isUpdating);


  const [activeTab, setActiveTab] = useState<'total' | 'cohort'>('total');


  const [selectedCohortNo, setSelectedCohortNo] = useState<number | undefined>(undefined);


  const { data: myPageData } = useQuery<MyPageResponse>({
    queryKey: ['myPage'],
    queryFn: () => axiosInstance.get('/users/me').then((res) => (res as any).data),
    staleTime: 1000 * 60 * 30,
  });
  const myCohortNo = myPageData?.cohortGenerationNo ?? undefined;

  useEffect(() => {
    if (activeTab === 'cohort' && selectedCohortNo === undefined && myCohortNo) {
      setSelectedCohortNo(myCohortNo);
    }
  }, [activeTab, myCohortNo, selectedCohortNo]);


  const { data: cohortsData } = useQuery({
    queryKey: ['cohorts'],
    queryFn: fetchCohorts,
    staleTime: 1000 * 60 * 60,
    enabled: activeTab === 'cohort',
  });
  const cohorts: Cohort[] = cohortsData?.data || [];


  const queryKey =
    activeTab === 'cohort' ? ['ranking', 'cohort', selectedCohortNo] : ['ranking', 'total'];

  const { data, isLoading, isError } = useQuery<RankingResponse>({
    queryKey,
    queryFn: () => fetchRanking(activeTab, selectedCohortNo),
    staleTime: 1000 * 60 * 5,
    enabled: activeTab === 'total' || selectedCohortNo !== undefined,

    placeholderData: (previousData) => previousData,
  });

  const top100 = data?.data?.top100 || [];
  const myRanking = data?.data?.myRanking;


  const showSkeleton = isLoading && !data;


  const top3 = top100.filter((u: RankingUser) => u.rank <= 3);
  const restRanking = top100.filter((u: RankingUser) => u.rank > 3);


  const [isSyncing, setIsSyncing] = useState(false);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
  const addToast = useUIStore((state) => state.addToast);

  const handleForceSync = () => {
    if (isSyncing) return;
    setIsSyncModalOpen(true);
  };

  const onConfirmSync = async () => {
    setIsSyncing(true);
    try {
      await axiosInstance.post('/ranking/sync');
      qClient.invalidateQueries({ queryKey: ['ranking'] });
      addToast('전체 랭킹 동기화가 완료되었습니다! 🥇', 'success');
      setIsSyncModalOpen(false);
    } catch (err) {
      console.error('Sync error:', err);
      addToast('동기화 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="w-full max-w-[1240px] mx-auto py-8 px-4 md:px-6 relative">
      {}
      <div className="absolute top-[10%] left-[-10%] w-[500px] h-[500px] bg-primary-blue/10 rounded-full blur-[120px] pointer-events-none -z-10"></div>
      <div className="absolute bottom-[20%] right-[-10%] w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none -z-10"></div>

      <div className="min-h-[600px] rounded-[48px] glass-premium overflow-hidden relative z-10 transition-all duration-500">

        {}
        <div className="px-8 pt-8 flex items-center justify-between">
          <div className="flex flex-col">
            <h1 className="text-3xl font-black text-[var(--text-strong)] tracking-tight">실시간 랭킹</h1>
            <p className="text-sm text-[var(--text-subtle)] font-semibold mt-1">세이브박스 저축으로 매일 새로운 순위에 도전하세요.</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleForceSync}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-black shadow-sm transition-all ${
              isSyncing
                ? 'bg-[var(--surface-soft)] text-[var(--text-muted)] cursor-not-allowed'
                : 'bg-white text-[var(--accent)] border-2 border-[var(--accent-soft)] hover:border-[var(--accent)] hover:shadow-md'
            }`}
          >
            <motion.svg
              animate={isSyncing ? { rotate: 360 } : {}}
              transition={isSyncing ? { repeat: Infinity, duration: 1, ease: 'linear' } : {}}
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </motion.svg>
            {isSyncing ? '동기화 중...' : '랭킹 갱신'}
          </motion.button>
        </div>

        {}
        <div className="px-6 pt-6 pb-4 flex flex-col items-center gap-4">
          <div className="flex bg-[var(--surface-soft)] p-1 rounded-2xl w-full max-w-sm">
            {(['total', 'cohort'] as const).map((tab) => (
              <button
                key={tab}
                className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all duration-200 ${
                  activeTab === tab
                    ? 'bg-[var(--accent)] text-white shadow-[0_4px_12px_rgba(37,99,235,0.3)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-strong)]'
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {tab === 'total' ? '전체 랭킹' : '기수별 랭킹'}
              </button>
            ))}
          </div>

          {}
          {activeTab === 'cohort' && cohorts.length > 0 && (
            <select
              value={selectedCohortNo ?? ''}
              onChange={(e) => setSelectedCohortNo(Number(e.target.value))}
              className="w-full max-w-sm px-4 py-2.5 rounded-2xl border-2 border-[var(--line-soft)] bg-[var(--surface-base)] text-sm font-bold text-[var(--text-strong)] focus:border-[var(--accent)] outline-none transition-all cursor-pointer appearance-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%232563eb'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 14px center',
                backgroundSize: '18px',
              }}
            >
               {[...cohorts]
                .sort((a, b) => b.generationNo - a.generationNo)
                .map((c) => (
                  <option key={c.cohortId} value={c.generationNo}>
                    {c.generationNo}기{c.generationNo === myCohortNo ? ' (내 기수)' : ''}
                  </option>
                ))}
            </select>
          )}
        </div>

        {}
        {(activeTab === 'total' || selectedCohortNo === myCohortNo) && (
        <div className="mx-4 mb-6">
          <div className="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-[var(--accent)] via-[#1e5fd9] to-[var(--secondary-blue,#004ecc)] p-6 text-white shadow-[0_12px_40px_rgba(10,101,255,0.25)]">
            {}
            <div className="absolute -right-8 -top-8 w-40 h-40 rounded-full bg-white/5" />
            <div className="absolute -right-4 -bottom-10 w-32 h-32 rounded-full bg-white/5" />
            <div className="absolute left-1/2 top-0 w-28 h-28 rounded-full bg-white/5 -translate-x-1/2 -translate-y-1/2" />

            <div className="relative z-10">
              <p className="text-xs font-bold tracking-[0.1em] uppercase text-white/70 mb-3">
                {activeTab === 'total' ? '전체' : `${selectedCohortNo ?? myCohortNo}기`} 내 현재 랭킹
              </p>

              {showSkeleton ? (
                <div className="flex items-center gap-3 animate-pulse">
                  <div className="w-16 h-16 rounded-2xl bg-white/20" />
                  <div className="w-32 h-6 rounded-lg bg-white/20" />
                </div>
              ) : !myRanking || myRanking.rank === -1 ? (
                <div className="flex items-center gap-4">
                  <img
                    src="/assets/mascot_happy.png"
                    alt=""
                    className="w-16 h-16 object-contain drop-shadow-lg"
                    onError={(e) => (e.currentTarget.style.display = 'none')}
                  />
                  <div>
                    <p className="text-xl font-black">아직 랭킹이 없어요!</p>
                    <p className="text-sm text-white/70 mt-1 font-semibold">저축을 시작하고 랭킹을 올려보세요 🚀</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-5">
                    <div className="flex items-center gap-3">
                      <div className="flex items-baseline">
                        <span className="text-6xl font-black tracking-tight leading-none">{myRanking.rank}</span>
                        <span className="text-2xl font-bold ml-1 text-white/80">위</span>
                      </div>
                      {}
                      <div className="bg-white/20 backdrop-blur-sm rounded-lg px-2 py-1 h-fit transform scale-110 flex items-center gap-2">
                        <TrendBadge diff={myRanking.rankDiff} />
                        {isUpdating && (
                          <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                            className="w-3 h-3 border-2 border-white/50 border-t-white rounded-full"
                          />
                        )}
                      </div>
                    </div>
                    {myRanking.nickname && (
                      <span className="text-lg font-bold text-white/90">{myRanking.nickname}</span>
                    )}
                  </div>
                  {myRanking.cohortNo && (
                    <span className="text-sm bg-white/15 backdrop-blur-sm px-4 py-1.5 rounded-full font-bold border border-white/20">
                      {myRanking.cohortNo}기
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        )}

        {}
        {!showSkeleton && !isError && top3.length > 0 && (
          <Podium top3={top3} />
        )}

        {}
        <div className="px-6 pb-8">
          {showSkeleton && (
            <div className="flex flex-col gap-3 animate-pulse">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-[72px] rounded-2xl bg-[var(--surface-soft)]" />
              ))}
            </div>
          )}

          {isError && (
            <div className="text-center text-[var(--danger)] my-6 bg-[var(--surface-danger)] p-6 rounded-2xl text-sm font-bold border border-[var(--danger-soft)]">
              데이터를 불러오지 못했습니다.
            </div>
          )}

          {!showSkeleton && !isError && top100.length === 0 && (
            <div className="text-center text-[var(--text-subtle)] my-8 py-16 bg-[var(--surface-soft)] rounded-[28px] border-2 border-dashed border-[var(--line-soft)]">
              <p className="text-lg font-bold mb-1">아직 랭킹에 등록된 유저가 없습니다</p>
              <p className="text-sm text-[var(--text-muted)]">세이브박스에 저축을 시작해 보세요!</p>
            </div>
          )}

          {restRanking.length > 0 && (
            <LayoutGroup id="ranking-container">
              <motion.ul layout className="flex flex-col gap-3">
                <AnimatePresence mode="popLayout">
                  {restRanking.map((user: RankingUser) => (
                    <motion.li
                      layout
                      key={user.userId}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={{
                        type: 'spring',
                        stiffness: 300,
                        damping: 30,
                        mass: 1,
                        layout: { type: 'spring', stiffness: 300, damping: 30, mass: 1 }
                      }}
                      className="flex items-center justify-between p-5 rounded-[28px] glass-premium hover-glass transition-shadow duration-300 group cursor-default"
                    >
                      <div className="flex items-center gap-4">
                        <motion.span layout="position" className="w-9 h-9 flex items-center justify-center rounded-xl bg-[var(--surface-soft)] text-[var(--text-strong)] text-[15px] font-black flex-shrink-0">
                          {user.rank}
                        </motion.span>
                        <ProfileAvatar url={user.profileImageUrl} rank={user.rank} userId={user.userId} />
                        <motion.div layout="position" className="flex items-center gap-2">
                          <span className="font-extrabold text-[var(--text-strong)] text-[15px] group-hover:text-[var(--accent)] transition-colors">
                            {user.nickname || `유저 ${user.userId}`}
                          </span>
                          {user.cohortNo && (
                            <span className="text-[11px] font-bold text-[var(--accent)] bg-[var(--accent-soft)] px-2 py-0.5 rounded-lg">
                              {user.cohortNo}기
                            </span>
                          )}
                        </motion.div>
                      </div>

                      <motion.div layout="position">
                        <TrendBadge diff={user.rankDiff} />
                      </motion.div>
                    </motion.li>
                  ))}
                </AnimatePresence>
              </motion.ul>
            </LayoutGroup>
          )}
        </div>
      </div>

      {}
      <RankingSyncModal
        isOpen={isSyncModalOpen}
        onClose={() => setIsSyncModalOpen(false)}
        onConfirm={onConfirmSync}
        isSyncing={isSyncing}
      />
    </div>
  );
};

export default RankingPage;
