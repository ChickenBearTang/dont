import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components';
import { fetchOnboardingStatus } from '../api/userApi';
import { useToast } from '@/shared/hooks';
import { formatNumber } from '@/shared/utils';

export const FinanceConnectPage = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [recommendedAmount, setRecommendedAmount] = useState<number | null>(null);


  useEffect(() => {
    const handlePopState = (e: PopStateEvent) => {
      e.preventDefault();
      navigate('/onboarding', { replace: true });
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [navigate]);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetchOnboardingStatus();
        const { onboardingStatus, recommendedAmount: nextRecommendedAmount } = response.data;

        if (onboardingStatus === 'NOT_STARTED') {
          navigate('/onboarding', { replace: true });
          return;
        }

        if (onboardingStatus === 'COMPLETED') {
          navigate('/dashboard', { replace: true });
          return;
        }

        setRecommendedAmount(nextRecommendedAmount);
      } catch (error) {
        console.error('Failed to load finance-connect data:', error);
        toast.error('연동 정보를 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [navigate, toast]);

  const handleNext = async () => {
    navigate('/finance/savebox-setup');
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-[860px] mx-auto py-6 px-4 md:px-6">
        <div className="min-h-[520px] rounded-[36px] border border-line-soft bg-surface-base shadow-[0_26px_60px_rgba(15,23,42,0.08)] flex items-center justify-center text-text-subtle font-semibold">
          연동 페이지를 준비하고 있어요...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[860px] mx-auto py-6 px-4 md:px-6">
      <div className="min-h-[520px] rounded-[36px] border border-line-soft bg-gradient-to-b from-surface-base via-surface-base to-surface-muted shadow-[0_26px_60px_rgba(15,23,42,0.08)] px-6 py-8 md:px-10">
        <div className="max-w-[620px] mx-auto flex min-h-[420px] flex-col items-center justify-center text-center">
          <p className="text-[13px] font-black tracking-[0.08em] text-text-subtle mb-3">
            계좌 연동
          </p>
          <h2 className="text-[34px] font-black text-text-strong tracking-tight leading-tight mb-3">
            금융 연동을 진행할 차례예요
          </h2>
          <p className="text-[15px] font-semibold text-text-muted mb-8">
            추천 저축 금액을 확인하고, 계좌 연동을 시작해 보세요.
          </p>

          <div className="w-full rounded-[24px] border border-line-soft bg-surface-base p-6 shadow-[0_10px_24px_rgba(15,23,42,0.06)] mb-8">
            <p className="text-[12px] font-black tracking-[0.08em] text-text-subtle mb-2">
              나의 추천 저축액
            </p>
            <p className="text-[44px] font-black text-accent tracking-tight">
              {formatNumber(recommendedAmount ?? 0)}원
            </p>
          </div>

          <Button onClick={handleNext} className="max-w-[360px] h-[56px]">
            계좌 연동하기
          </Button>
        </div>
      </div>
    </div>
  );
};
