import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, Input, Button } from '@/shared/components';
import { useToast } from '@/shared/hooks';
import { fetchOnboardingStatus, completeOnboarding } from '@/features/user/api/userApi';
import { useGetSavingsSetting, useGetMyAccounts } from '../hooks/useAccountQueries';
import { useSaveSavingsSetting } from '../hooks/useAccountMutations';


export const SavingsRuleSetupPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: initialSetting, isLoading: isFetchingSetting } = useGetSavingsSetting();
  const { data: accounts, isLoading: isFetchingAccounts } = useGetMyAccounts();
  const { data: onboardingData, isLoading: isFetchingOnboarding } = useQuery({
    queryKey: ['onboardingStatus'],
    queryFn: fetchOnboardingStatus,
    select: (res) => res.data,
    staleTime: 0,
  });

  const { mutate: saveSetting, isPending: isSubmitting } = useSaveSavingsSetting();
  const { success, error: toastError } = useToast();


  const [keyword, setKeyword] = useState('삼성SSAFY');
  const [amount, setAmount] = useState<number>(0);
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isInitialized = useRef(false);

  useEffect(() => {
    if (initialSetting) return;

    const handlePopState = (e: PopStateEvent) => {
      e.preventDefault();
      navigate('/onboarding', { replace: true });
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [navigate, initialSetting]);


  useEffect(() => {
    if (isInitialized.current) return;

    if (isFetchingOnboarding || isFetchingSetting) return;


    if (initialSetting) {
      setKeyword(initialSetting.keyword || '삼성SSAFY');
      setIsActive(initialSetting.isActive ?? true);
    }


    if (onboardingData?.recommendedAmount) {
      setAmount(onboardingData.recommendedAmount);
    } else if (initialSetting?.savingsAmount) {
      setAmount(initialSetting.savingsAmount);
    }

    isInitialized.current = true;
  }, [initialSetting, onboardingData, isFetchingOnboarding, isFetchingSetting]);

  const primaryAccount = accounts?.find(
    (a) => !a.accountName.includes('세이브박스') && !a.accountTypeName.includes('세이브박스')
  );
  const saveboxAccount = accounts?.find(
    (a) => a.accountName.includes('세이브박스') || a.accountTypeName.includes('세이브박스')
  );

  const isFetching = isFetchingSetting || isFetchingAccounts || isFetchingOnboarding;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!keyword.trim()) {
      setError('저축할 키워드를 입력해주세요.');
      return;
    }

    if (amount <= 0) {
      setError('저축할 금액을 입력해주세요.');
      return;
    }

    if (!primaryAccount || !saveboxAccount) {
      toastError('연동된 계좌 정보를 찾을 수 없습니다.');
      return;
    }

    saveSetting(
      {
        primaryAccountId: primaryAccount.id,
        saveboxAccountId: saveboxAccount.id,
        keyword: keyword.trim(),
        savingsAmount: amount,
        isActive,
      },
      {
        onSuccess: async () => {
          if (initialSetting) {

            success('자동 저축 규칙이 변경되었습니다.');
            navigate('/finance/savebox');
          } else {

            try {
              await completeOnboarding();
              success('자동 저축 규칙이 저장되었습니다! 모든 온보딩이 완료되었습니다.');
              navigate('/dashboard');
            } catch (err) {
              console.error('Failed to complete onboarding status:', err);
              success('자동 저축 규칙이 저장되었습니다!');
              navigate('/dashboard');
            }
          }
        },
        onError: () => {
          toastError('규칙 저장 중 오류가 발생했습니다.');
        },
      }
    );
  };

  if (isFetching) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-primary-blue border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-gray font-medium">설정 정보를 불러오는 중...</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-6 py-12 flex flex-col min-h-screen">
      <div className="mb-10">
        <h1 className="text-2xl font-black text-eel mb-3 leading-tight">
          {initialSetting ? (
            '자동 저축 규칙 변경하기'
          ) : (
            <>
              나만의 자동 저축 규칙을
              <br />
              설정해볼까요?
            </>
          )}
        </h1>
        <p className="text-gray text-sm leading-relaxed">
          {initialSetting
            ? '설정된 키워드와 금액을 자유롭게 변경하여 스마트하게 저축하세요.'
            : (
              <>
                지정한 키워드가 포함된 입금이 발생할 때마다
                <br />
                설정한 금액이 자동으로 세이브박스에 저축됩니다.
              </>
            )}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        <div className="space-y-8 flex-1">
          {}
          <div className="grid grid-cols-2 gap-3">
            <Card className="p-4 border-2 border-line-thin bg-surface-soft">
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2 block">
                출금 계좌 (주계좌)
              </span>
              <p className="text-sm font-black text-text-strong truncate">
                {primaryAccount?.accountName}
              </p>
            </Card>
            <Card className="p-4 border-2 border-line-thin bg-surface-soft">
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-2 block">
                입금 계좌 (세이브박스)
              </span>
              <p className="text-sm font-black text-text-strong truncate">
                {saveboxAccount?.accountName}
              </p>
            </Card>
          </div>

          <div className="space-y-6">
            <Input
              label="저축 키워드"
              placeholder="예: 월급, 보너스, 용돈"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              hint="해당 단어가 입금 내역에 포함되면 저축이 실행됩니다."
            />

            <Input
              label="저축 금액"
              type="number"
              placeholder="저축할 금액을 입력하세요"
              value={amount || ''}
              onChange={(e) => setAmount(Number(e.target.value))}
              unit="원"
              hint="입금될 때마다 이만큼씩 저축할게요."
            />

            <div className="flex items-center justify-between p-4 bg-surface-soft rounded-2xl border border-line-soft">
              <div>
                <span className="text-sm font-bold text-text-strong block">규칙 활성화</span>
                <span className="text-[11px] text-text-muted">지금 바로 저축을 시작할까요?</span>
              </div>
              <button
                type="button"
                onClick={() => setIsActive(!isActive)}
                className={`w-12 h-6 rounded-full transition-colors relative ${isActive ? 'bg-primary-blue' : 'bg-line-strong'
                  }`}
              >
                <div
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${isActive ? 'right-1' : 'left-1'
                    }`}
                />
              </button>
            </div>

            {error && (
              <div className="p-4 bg-surface-danger/10 text-danger text-sm font-bold rounded-xl border border-danger-soft animate-in fade-in slide-in-from-top-1">
                ⚠️ {error}
              </div>
            )}
          </div>
        </div>

        <div className="mt-12">
          <Button type="submit" disabled={isSubmitting || !keyword || !amount}>
            {isSubmitting ? '설정 저장 중...' : initialSetting ? '규칙 변경하기' : '규칙 저장하기'}
          </Button>
        </div>
      </form>
    </div>
  );
};
