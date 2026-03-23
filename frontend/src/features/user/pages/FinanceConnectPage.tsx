import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components';
import { completeOnboarding, fetchOnboardingStatus } from '../api/userApi';
import { useToast } from '@/shared/hooks';
import { formatNumber } from '@/shared/utils';

export const FinanceConnectPage = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recommendedAmount, setRecommendedAmount] = useState<number | null>(null);

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
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await completeOnboarding();
      if (response.success && response.data.onboardingStatus === 'COMPLETED') {
        navigate('/dashboard', { replace: true });
      } else {
        toast.error('완료 처리에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      toast.error('완료 처리에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
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
            FINANCE CONNECT (TEMP)
          </p>
          <h2 className="text-[34px] font-black text-text-strong tracking-tight leading-tight mb-3">
            금융 연동을 진행할 차례예요
          </h2>
          <p className="text-[15px] font-semibold text-text-muted mb-8">
            현재는 임시 화면입니다. 저장된 추천 저축 금액을 확인한 뒤 다음으로 진행합니다.
          </p>

          <div className="w-full rounded-[24px] border border-line-soft bg-surface-base p-6 shadow-[0_10px_24px_rgba(15,23,42,0.06)] mb-8">
            <p className="text-[12px] font-black tracking-[0.08em] text-text-subtle mb-2">
              SAVED RECOMMENDATION
            </p>
            <p className="text-[44px] font-black text-accent tracking-tight">
              {formatNumber(recommendedAmount ?? 0)}원
            </p>
          </div>

          <Button onClick={handleNext} className="max-w-[360px] h-[56px]" disabled={isSubmitting}>
            {isSubmitting ? '처리 중...' : '다음'}
          </Button>
        </div>
      </div>
    </div>
  );
};
