import React from 'react';
import { useGetMyAccounts } from '../hooks/useAccountQueries';
import { AccountCard } from './AccountCard';

/**
 * 로딩 중일 때 표시할 스켈레톤 UI
 */
const AccountSkeleton = () => (
  <div className="w-full p-6 bg-white border border-light-gray rounded-2xl animate-pulse">
    <div className="flex justify-between mb-4">
      <div className="space-y-3">
        <div className="h-3 w-20 bg-light-gray rounded" />
        <div className="h-5 w-32 bg-light-gray rounded" />
        <div className="h-3 w-40 bg-light-gray rounded" />
      </div>
      <div className="w-10 h-10 rounded-full bg-light-gray" />
    </div>
    <div className="flex justify-end mt-8">
      <div className="h-8 w-32 bg-light-gray rounded" />
    </div>
  </div>
);

/**
 * 내 계좌 목록을 보여주는 컨테이너 컴포넌트
 */
export const AccountList: React.FC = () => {
  const { data: accounts, isLoading, isError, refetch } = useGetMyAccounts();

  // 1. 로딩 상태 처리
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <AccountSkeleton key={i} />
        ))}
      </div>
    );
  }

  // 2. 에러 상태 처리
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center bg-white border border-light-gray rounded-2xl">
        <div className="mb-4 text-4xl">⚠️</div>
        <h3 className="mb-2 text-lg font-bold text-eel">계좌 정보를 불러오지 못했습니다.</h3>
        <p className="mb-6 text-gray">일시적인 오류일 수 있으니 다시 시도해 주세요.</p>
        <button
          onClick={() => void refetch()}
          className="px-6 py-2 text-white transition-colors bg-primary-blue rounded-lg hover:bg-secondary-blue"
        >
          다시 시도
        </button>
      </div>
    );
  }

  // 3. 데이터가 없는 상태 처리
  if (!accounts || accounts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center bg-blue-bg/30 border-2 border-dashed border-light-gray rounded-2xl">
        <div className="mb-4 text-4xl">🏦</div>
        <h3 className="mb-2 text-lg font-bold text-gray">연결된 계좌가 없습니다.</h3>
        <p className="mb-6 text-gray">오픈뱅킹 연동을 통해 계좌를 등록해 보세요.</p>
        <button className="px-6 py-2 font-medium text-primary-blue transition-colors border-2 border-primary-blue rounded-lg hover:bg-primary-blue hover:text-white">
          계좌 등록하기
        </button>
      </div>
    );
  }

  // 4. 성공 상탱: 리스트 렌더링
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between px-2">
        <h2 className="text-xl font-black text-eel">
          내 계좌 <span className="text-primary-blue">{accounts.length}</span>
        </h2>
        <button
          onClick={() => void refetch()}
          className="text-sm font-bold text-gray hover:text-primary-blue transition-colors"
        >
          새로고침
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {accounts.map((account) => (
          <AccountCard key={account.accountNo} account={account} />
        ))}
      </div>
    </div>
  );
};
