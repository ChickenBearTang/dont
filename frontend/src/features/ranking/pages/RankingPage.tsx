import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRankingSse, type RankingUser } from '../hooks/useRankingSse';
import axiosInstance from '@/shared/api/axiosInstance';

// 백엔드(CommonResponse)에서 내려주는 JSON 포맷 인터페이스
interface RankingResponse {
  status: string;
  message: string;
  data: {
    top10: RankingUser[];
    myRanking: RankingUser;
  };
}

// 초기 데이터 조회 Fetcher (axiosInstance를 사용하여 자동으로 JWT 토큰 첨부)
const fetchRanking = async (type: 'total' | 'cohort'): Promise<RankingResponse> => {
  return await axiosInstance.get(`/ranking/${type}`);
};

export const RankingPage = () => {
  // 1. [실시간 파이프라인 결합] 🎉
  // 이 훅은 조용히 백그라운드에서 SSE(/api/ranking/stream)를 수신하며,
  // 랭킹 변동 알림이 오면 아래 React Query 캐시를 가로채서 화면을 리렌더링 시킵니다.
  useRankingSse();

  // 2. [탭 상태 관리]
  const [activeTab, setActiveTab] = useState<'total' | 'cohort'>('total');

  // 3. [초기 데이터 페칭]
  const queryKey = ['ranking', activeTab];

  const { data, isLoading, isError } = useQuery<RankingResponse>({
    queryKey,
    queryFn: () => fetchRanking(activeTab),
    staleTime: 1000 * 60 * 5, // 5분 동안 캐시 유지 (나머지는 SSE가 업데이트 책임짐)
  });

  const top10 = data?.data?.top10 || [];
  const myRanking = data?.data?.myRanking;

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-800 font-sans">
      {/* --- 상단: 탭 전환 (전체 랭킹 / 우리 기수 랭킹) --- */}
      <header className="p-4 bg-white shadow-sm flex flex-col items-center">
        <h1 className="text-xl font-bold mb-4">🏆 실시간 세이브박스 랭킹</h1>
        <div className="flex justify-center space-x-2 bg-gray-100 p-1 py-1 px-1 rounded-full w-full max-w-sm">
          <button
            className={`flex-1 py-2 rounded-full text-sm font-semibold transition-all ${
              activeTab === 'total'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-gray-500 hover:text-gray-800'
            }`}
            onClick={() => setActiveTab('total')}
          >
            전체 랭킹
          </button>
          <button
            className={`flex-1 py-2 rounded-full text-sm font-semibold transition-all ${
              activeTab === 'cohort'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-gray-500 hover:text-gray-800'
            }`}
            onClick={() => setActiveTab('cohort')}
          >
            기수별 랭킹
          </button>
        </div>
      </header>

      {/* --- 중단: 내 랭킹 정보 (Hero 섹션) --- */}
      <section className="m-4 p-5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-lg text-white">
        <h2 className="text-sm opacity-80 mb-1">내 현재 랭킹</h2>
        {isLoading ? (
          <p className="text-lg font-medium animate-pulse">데이터 로딩 중...</p>
        ) : !myRanking || myRanking.rank === -1 ? (
          <div className="mt-2">
            <p className="text-xl font-bold">아직 랭킹이 없어요!</p>
            <p className="text-sm opacity-80 mt-1">저축을 시작하고 랭킹을 올려보세요 🚀</p>
          </div>
        ) : (
          <div className="flex justify-between items-end mt-2 animate-fade-in-up">
            <div>
              <span className="text-5xl font-extrabold">{myRanking.rank}</span>
              <span className="text-xl ml-1 font-medium">위</span>
            </div>
            <div className="text-right">
              <span className="text-xs opacity-80 block mb-1">누적 저축액</span>
              <span className="text-xl font-bold">{myRanking.score.toLocaleString()} 원</span>
            </div>
          </div>
        )}
      </section>

      {/* --- 하단: Top 10 리스트 --- */}
      <section className="flex-1 overflow-y-auto px-4 pb-10">
        <h3 className="text-sm font-bold text-gray-500 mb-3 ml-1 uppercase tracking-wider">
          Top 10 랭커 리스트
        </h3>

        {isLoading && (
          <div className="flex justify-center items-center h-40">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}

        {isError && (
          <p className="text-center text-red-500 my-10 bg-red-50 p-4 rounded-xl text-sm">
            데이터를 불러오지 못했습니다.
          </p>
        )}

        {!isLoading && !isError && top10.length === 0 && (
          <p className="text-center text-gray-500 my-10 py-10 bg-white rounded-xl shadow-sm">
            아직 랭킹에 등록된 유저가 없습니다.
          </p>
        )}

        <ul className="space-y-3">
          {top10.map((user) => (
            <li
              key={user.userId}
              className={`flex items-center justify-between p-4 bg-white rounded-2xl shadow-sm border ${
                user.rank === 1
                  ? 'border-yellow-400 bg-yellow-50/50'
                  : user.rank === 2
                    ? 'border-gray-300 bg-gray-50/50'
                    : user.rank === 3
                      ? 'border-amber-600 bg-amber-50/50'
                      : 'border-transparent'
              } transition-transform hover:scale-[1.01]`}
            >
              <div className="flex items-center space-x-4">
                <span
                  className={`w-8 h-8 flex items-center justify-center rounded-xl font-bold text-sm ${
                    user.rank === 1
                      ? 'bg-yellow-400 text-yellow-900'
                      : user.rank === 2
                        ? 'bg-gray-300 text-gray-800'
                        : user.rank === 3
                          ? 'bg-amber-600 text-orange-100'
                          : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {user.rank}
                </span>
                <span className="font-semibold text-gray-800">
                  {user.nickname || `유저 ${user.userId}`}
                </span>
              </div>
              <span className="font-bold text-indigo-600">
                {user.score.toLocaleString()}
                <span className="text-xs font-normal text-gray-500 ml-1">원</span>
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default RankingPage;
