import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetMyAccounts } from '../hooks/useAccountQueries';
import { useSetPrimaryAccount, useCreateSaveBox } from '../hooks/useAccountMutations';
import type { AccountDetail } from '../types';

/**
 * 전용 선택 가능 계좌 카드 컴포넌트
 */
const SelectableAccountCard: React.FC<{
  account: AccountDetail;
  isSelected: boolean;
  onSelect: () => void;
}> = ({ account, isSelected, onSelect }) => {
  const { bankName, accountName, accountNo, accountBalance } = account;
  const formattedBalance = Number(accountBalance).toLocaleString();

  return (
    <div
      onClick={onSelect}
      className={`w-full p-5 transition-all border-2 rounded-2xl cursor-pointer flex items-center justify-between ${
        isSelected
          ? 'border-primary-blue bg-blue-bg shadow-md'
          : 'border-light-gray bg-white hover:border-primary-blue/30'
      }`}
    >
      <div className="flex flex-col">
        <span className="text-xs font-medium text-gray mb-1">{bankName}</span>
        <h3 className="text-base font-bold text-eel mb-0.5">{accountName}</h3>
        <p className="text-xs text-gray font-mono">{accountNo}</p>
      </div>
      <div className="flex flex-col items-end">
        <div className="flex items-baseline gap-0.5">
          <span className="text-lg font-black text-eel">{formattedBalance}</span>
          <span className="text-sm font-bold text-eel">원</span>
        </div>
        <div
          className={`mt-2 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
            isSelected ? 'border-primary-blue bg-primary-blue' : 'border-gray bg-transparent'
          }`}
        >
          {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
        </div>
      </div>
    </div>
  );
};

/**
 * 세이브박스 개설 및 주계좌 설정 온보딩 페이지
 */
export const SaveboxSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);

  // 데이터 조회
  const { data: accounts, isLoading, isError } = useGetMyAccounts();

  // Mutations
  const { mutateAsync: setPrimary } = useSetPrimaryAccount();
  const { mutateAsync: createSaveBox } = useCreateSaveBox();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSetup = async () => {
    if (!selectedAccountId) return;

    try {
      setIsSubmitting(true);
      // 1. 주계좌 설정
      await setPrimary(selectedAccountId);
      // 2. 세이브박스 개설 (백엔드 스펙에 맞춰 accountTypeUniqueNo 전달)
      await createSaveBox({ accountTypeUniqueNo: '999-1-792bcf290d6a48' });

      // 성공 상태로 전환
      setIsSuccess(true);
    } catch (error) {
      console.error('Onboarding Setup Failed:', error);
      alert('설정 중 오류가 발생했습니다. 다시 시도해 주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center animate-in fade-in zoom-in duration-500">
        <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mb-8 relative">
          <div className="absolute inset-0 bg-green-200 rounded-full animate-ping opacity-25" />
          <svg
            className="w-12 h-12 text-green-500 relative z-10"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={3}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-3xl font-black text-eel mb-4">세이브박스 개설 완료!</h2>
        <p className="text-gray text-lg mb-10 leading-relaxed">
          이제 돈을 더 똑똑하게 모을 준비가 되었어요.
          <br />주 계좌와 연결되어 자동으로 저축이 시작됩니다.
        </p>
        <button
          onClick={() => navigate('/savings-rule-setup')}
          className="w-full max-w-xs py-4 bg-primary-blue text-white rounded-2xl text-lg font-bold shadow-lg hover:shadow-primary-blue/30 transition-all hover:scale-[1.02]"
        >
          자동 저축 규칙 설정하기
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-primary-blue border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-gray font-medium">계좌 목록을 불러오는 중...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
        <div className="text-red-500 mb-4 text-4xl">⚠️</div>
        <h2 className="text-xl font-bold text-eel mb-2">계좌 정보를 불러올 수 없습니다.</h2>
        <p className="text-gray mb-6">금융사 연결 상태를 확인하거나 잠시 후 다시 시도해 주세요.</p>
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-2 bg-primary-blue text-white rounded-lg font-bold"
        >
          새로고침
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-6 py-12 flex flex-col min-h-screen">
      <div className="mb-10 text-center">
        <h1 className="text-2xl font-black text-eel mb-3 leading-tight">
          돈을 모을 세이브박스를 개설하고,
          <br />
          연결할 주 계좌를 선택해 주세요.
        </h1>
        <p className="text-gray text-sm leading-relaxed">
          주 계좌는 저축할 돈이 빠져나가는 계좌입니다.
          <br />
          원하는 계좌를 하나 선택해 주세요.
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pb-32">
        {accounts?.map((account) => (
          <SelectableAccountCard
            key={account.id}
            account={account}
            isSelected={selectedAccountId === account.id}
            onSelect={() => setSelectedAccountId(account.id)}
          />
        ))}

        {accounts?.length === 0 && (
          <div className="text-center py-10 bg-blue-bg rounded-2xl border-2 border-dashed border-light-gray">
            <p className="text-gray text-sm">연결된 계좌가 없습니다.</p>
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white to-transparent pointer-events-none">
        <div className="max-w-md mx-auto pointer-events-auto">
          <button
            onClick={handleSetup}
            disabled={!selectedAccountId || isSubmitting}
            className={`w-full py-4 rounded-2xl text-lg font-bold transition-all ${
              !selectedAccountId || isSubmitting
                ? 'bg-light-gray text-gray cursor-not-allowed'
                : 'bg-primary-blue text-white shadow-lg hover:shadow-primary-blue/30 scale-100 hover:scale-[1.02]'
            }`}
          >
            {isSubmitting ? '세이브박스 개설 중...' : '세이브박스 개설하기'}
          </button>
        </div>
      </div>
    </div>
  );
};
