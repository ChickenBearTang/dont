import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';
import { fetchOnboardingStatus, submitOnboarding } from '../api/userApi';
import { useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/shared/hooks';
import { formatNumber } from '@/shared/utils';

const KDT_MONTHLY_INCOME = 1_300_000;
const DEFAULT_MONTHLY_INCOME = 1_000_000;
const RECOMMEND_RATIO = 0.3;
const TOTAL_STEPS = 4;
const FIXED_COST_OPTIONS = [50000, 100000, 150000, 200000, 250000, 300000, 400000, 500000];
const VARIABLE_COST_OPTIONS = [50000, 100000, 150000, 200000, 250000, 300000, 400000, 500000];

export const OnboardingPage = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const queryClient = useQueryClient();

  const [step, setStep] = useState(() => Number(sessionStorage.getItem('onboarding_step')) || 1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isKdt, setIsKdt] = useState<boolean | null>(() => {
    const saved = sessionStorage.getItem('onboarding_isKdt');
    return saved === null ? null : saved === 'true';
  });
  const [fixedCostInput, setFixedCostInput] = useState(() => sessionStorage.getItem('onboarding_fixedCost') || '');
  const [variableCostInput, setVariableCostInput] = useState(() => sessionStorage.getItem('onboarding_variableCost') || '');

  const [serverRecommendedAmount, setServerRecommendedAmount] = useState<number | null>(null);


  useEffect(() => {
    const handlePopState = (e: PopStateEvent) => {
      if (step > 1) {
        e.preventDefault();
        setStep((prev) => Math.max(1, prev - 1));
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [step]);


  useEffect(() => {
    if (isKdt !== null) sessionStorage.setItem('onboarding_isKdt', String(isKdt));
    sessionStorage.setItem('onboarding_fixedCost', fixedCostInput);
    sessionStorage.setItem('onboarding_variableCost', variableCostInput);
    sessionStorage.setItem('onboarding_step', String(step));
  }, [isKdt, fixedCostInput, variableCostInput, step]);


  const changeStep = (nextStep: number) => {
    if (nextStep > step) {
      window.history.pushState({ step: nextStep }, '', window.location.pathname);
    }
    setStep(nextStep);
  };

  const resolveErrorMessage = (error: unknown) => {
    if (typeof error !== 'object' || error === null || !('response' in error)) {
      return undefined;
    }

    const response = (error as { response?: { data?: { message?: string } } }).response;
    const message = response?.data?.message;
    return typeof message === 'string' && message.trim() ? message : undefined;
  };

  useEffect(() => {
    const loadOnboardingStatus = async () => {
      try {
        const statusResponse = await fetchOnboardingStatus();
        const onboardingStatus = statusResponse.data.onboardingStatus;

        if (onboardingStatus === 'COMPLETED') {
          navigate('/dashboard', { replace: true });
          return;
        }

        if (onboardingStatus === 'IN_PROGRESS') {

          if (statusResponse.data.recommendedAmount) {
            setServerRecommendedAmount(statusResponse.data.recommendedAmount);
          }

          if (step === 1) setStep(4);
        }
      } catch (error) {
        console.error('Failed to load onborading data:', error);
        toast.error(resolveErrorMessage(error) ?? '온보딩 정보를 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    void loadOnboardingStatus();
  }, [navigate, toast]);

  const fixedCost = Number(fixedCostInput || 0);
  const variableCost = Number(variableCostInput || 0);

  const monthlyIncome = useMemo(() => {
    if (isKdt === null) {
      return 0;
    }
    return isKdt ? KDT_MONTHLY_INCOME : DEFAULT_MONTHLY_INCOME;
  }, [isKdt]);

  const availableAmount = Math.max(0, monthlyIncome - fixedCost - variableCost);
  const recommendedAmount = Math.max(
    0,
    Math.floor((availableAmount * RECOMMEND_RATIO) / 1000) * 1000
  );

  const handleCompleteOnboarding = async (selectedVariableCost?: number) => {
    if (isSubmitting) {
      return;
    }

    const nextVariableCost =
      typeof selectedVariableCost === 'number' ? selectedVariableCost : variableCost;
    const nextAvailableAmount = Math.max(0, monthlyIncome - fixedCost - nextVariableCost);
    const nextRecommendedAmount = Math.max(
      0,
      Math.floor((nextAvailableAmount * RECOMMEND_RATIO) / 1000) * 1000
    );

    setVariableCostInput(String(nextVariableCost));

    setIsSubmitting(true);
    try {
      const response = await submitOnboarding({ recommendedAmount: nextRecommendedAmount });
      if (
        response.success &&
        (response.data.onboardingStatus === 'IN_PROGRESS' || response.data.onboardingCompleted)
      ) {

        void queryClient.invalidateQueries({ queryKey: ['onboardingStatus'] });
        setStep(4);
      }
    } catch (error) {
      console.error('Failed to submit onboarding:', error);
      toast.error(resolveErrorMessage(error) ?? '정보 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = Math.min((step / TOTAL_STEPS) * 100, 100);

  if (isLoading) {
    return (
      <div className="w-full max-w-[860px] mx-auto py-6 px-4 md:px-6">
        <div className="min-h-[620px] rounded-[36px] border border-line-soft bg-surface-base shadow-[0_26px_60px_rgba(15,23,42,0.08)] flex items-center justify-center text-text-subtle font-semibold">
          온보딩을 준비하고 있어요...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[860px] mx-auto py-6 px-4 md:px-6">
      <div className="min-h-[660px] rounded-[36px] border border-line-soft bg-gradient-to-b from-surface-base via-surface-base to-surface-muted shadow-[0_26px_60px_rgba(15,23,42,0.08)] px-4 py-5 md:px-10 md:py-8 relative overflow-hidden">
        <div className="pointer-events-none absolute -right-20 -top-24 h-72 w-72 rounded-full bg-accent-soft/60 blur-3xl" />
        <div className="pointer-events-none absolute -left-24 -bottom-28 h-72 w-72 rounded-full bg-surface-soft/80 blur-3xl" />

        {step <= TOTAL_STEPS && (
          <div className="relative z-10">
            <div className={`flex items-center gap-3 mb-6 ${step === 1 ? 'justify-end' : ''}`}>
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep((prev) => prev - 1)}
                  className="h-10 w-10 rounded-full border border-line-soft bg-surface-base text-text-muted hover:text-text-strong hover:border-line-strong transition-colors"
                >
                  ←
                </button>
              )}
              <div className="flex-1 h-3 rounded-full bg-surface-soft overflow-hidden">
                <div
                  className="h-full rounded-full bg-accent transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-[13px] font-extrabold text-accent min-w-[62px] text-right">
                {step}/{TOTAL_STEPS}
              </span>
            </div>
          </div>
        )}

        <div className="relative z-10 min-h-[560px] flex flex-col justify-between">
          {step === 1 && (
            <div className="max-w-[640px] mx-auto w-full animate-in fade-in slide-in-from-right-4 duration-500 pt-2 md:pt-4">
              <div className="flex flex-col items-center text-center mb-10">
                <Mascot src="/assets/mascot_happy.png" className="mb-3" />
                <h2 className="text-[32px] md:text-[36px] font-black text-text-strong tracking-tight mb-3 leading-tight">
                  KDT에 참여 중이신가요?
                </h2>
                <p className="text-[15px] text-text-muted font-semibold">
                  참여 여부에 따라 월 소득 기준이 달라져요.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-7">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsKdt(true);
                    setStep(2);
                  }}
                  className="h-[88px] rounded-[20px] text-[24px] font-black"
                >
                  네
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsKdt(false);
                    setStep(2);
                  }}
                  className="h-[88px] rounded-[20px] text-[24px] font-black"
                >
                  아니요
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="max-w-[640px] mx-auto w-full animate-in fade-in slide-in-from-right-4 duration-500 pt-2 md:pt-4">
              <div className="flex flex-col items-center text-center mb-10">
                <Mascot src="/assets/mascot_happy.png" className="mb-3" />
                <h2 className="text-[32px] md:text-[36px] font-black text-text-strong tracking-tight mb-3 leading-tight">
                  월 고정비를 알려주세요
                </h2>
                <p className="text-[15px] text-text-muted font-semibold">
                  월세, 통신비, 보험료처럼 매달 고정으로 나가는 금액이에요.
                </p>
              </div>

              <div
                className="w-full max-w-[720px] mx-auto mb-10 grid gap-3"
                style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}
              >
                {FIXED_COST_OPTIONS.map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant="outline"
                    fullWidth={false}
                    onClick={() => {
                      setFixedCostInput(String(preset));
                      changeStep(3);
                    }}
                    className="w-full h-[88px] rounded-[20px] text-[20px] font-black"
                  >
                    {formatNumber(preset)}원
                  </Button>
                ))}
              </div>

              <div className="w-full max-w-[720px] mx-auto pt-6 border-t border-line-soft">
                <p className="text-center text-[13px] font-bold text-text-muted mb-4 uppercase tracking-wider">
                  또는 직접 입력하기
                </p>
                <div className="flex flex-col gap-4">
                  <div className="relative group">
                    <input
                      type="text"
                      inputMode="numeric"
                      value={fixedCostInput ? Number(fixedCostInput).toLocaleString() : ''}
                      onChange={(e) => {
                        const val = e.target.value.replace(/[^0-9]/g, '');
                        setFixedCostInput(val);
                      }}
                      className="w-full h-[80px] rounded-[24px] border-2 border-line-soft bg-surface-base px-8 text-[32px] font-black outline-none transition-all focus:border-accent text-text-strong pr-16"
                      placeholder="0"
                    />
                    <span className="absolute right-8 top-1/2 -translate-y-1/2 text-[24px] font-black text-text-muted">원</span>
                  </div>
                  <Button
                    type="button"
                    disabled={!fixedCostInput || Number(fixedCostInput) <= 0}
                    onClick={() => changeStep(3)}
                    className="h-[64px] rounded-[22px] text-lg"
                  >
                    입력 완료
                  </Button>
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="max-w-[640px] mx-auto w-full animate-in fade-in slide-in-from-right-4 duration-500 pt-2 md:pt-4">
              <div className="flex flex-col items-center text-center mb-10">
                <Mascot src="/assets/mascot_happy.png" className="mb-3" />
                <h2 className="text-[32px] md:text-[36px] font-black text-text-strong tracking-tight mb-3 leading-tight">
                  고정비를 제외한 월 평균 지출은 어느 정도인가요?
                </h2>
                <p className="text-[15px] text-text-muted font-semibold">
                  식비, 생활비, 취미 생활 등 매달 나가는 평균적인 지출액을 알려주세요.
                </p>
              </div>


              <div
                className="w-full max-w-[720px] mx-auto mb-10 grid gap-3"
                style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))' }}
              >
                {VARIABLE_COST_OPTIONS.map((preset) => (
                  <Button
                    key={preset}
                    type="button"
                    variant="outline"
                    fullWidth={false}
                    disabled={isSubmitting}
                    onClick={() => void handleCompleteOnboarding(preset)}
                    className="w-full h-[88px] rounded-[20px] text-[20px] font-black"
                  >
                    {formatNumber(preset)}원
                  </Button>
                ))}
              </div>

              <div className="w-full max-w-[720px] mx-auto pt-6 border-t border-line-soft">
                <p className="text-center text-[13px] font-bold text-text-muted mb-4 uppercase tracking-wider">
                  또는 직접 입력하기
                </p>
                <div className="flex flex-col gap-4">
                  <div className="relative">
                    <input
                      type="text"
                      inputMode="numeric"
                      value={variableCostInput ? Number(variableCostInput).toLocaleString() : ''}
                      onChange={(e) => {
                        const val = e.target.value.replace(/[^0-9]/g, '');
                        setVariableCostInput(val);
                      }}
                      className="w-full h-[80px] rounded-[24px] border-2 border-line-soft bg-surface-base px-8 text-[32px] font-black outline-none transition-all focus:border-accent text-text-strong pr-16"
                      placeholder="0"
                    />
                    <span className="absolute right-8 top-1/2 -translate-y-1/2 text-[24px] font-black text-text-muted">원</span>
                  </div>
                  <Button
                    type="button"
                    disabled={!variableCostInput || Number(variableCostInput) <= 0 || isSubmitting}
                    onClick={() => void handleCompleteOnboarding()}
                    className="h-[64px] rounded-[22px] text-lg"
                  >
                    {isSubmitting ? '저장 중...' : '계산하기'}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="max-w-[660px] mx-auto w-full flex flex-col items-center text-center animate-in fade-in zoom-in duration-500 py-3">
              <Mascot
                src="/assets/mascot_happy.png"
                speech="입력해주신 정보를 바탕으로 추천 저축액을 계산했어요."
                className="mb-8"
              />

              <div className="w-full bg-surface-base rounded-[30px] p-8 border border-line-soft shadow-[0_14px_30px_rgba(15,23,42,0.08)] mb-8">
                <p className="text-[12px] text-text-subtle font-black tracking-[0.08em] mb-2">
                  추천 저축액
                </p>
                <p className="text-5xl font-black text-accent tracking-tight">
                  {formatNumber(recommendedAmount || serverRecommendedAmount || 0)}원
                </p>
                {}
                {monthlyIncome > 0 && (
                  <div className="mt-7 grid sm:grid-cols-2 gap-3 text-sm text-text-muted font-semibold">
                    <p className="rounded-2xl bg-surface-muted px-4 py-3">
                      기준 월 소득: {formatNumber(monthlyIncome)}원
                    </p>
                    <p className="rounded-2xl bg-surface-muted px-4 py-3">
                      월 고정비: {formatNumber(fixedCost)}원
                    </p>
                    <p className="rounded-2xl bg-surface-muted px-4 py-3">
                      월 평균 지출 (고정비 제외): {formatNumber(variableCost)}원
                    </p>
                    <p className="rounded-2xl bg-accent-soft text-accent px-4 py-3">
                      월 가용금액: {formatNumber(availableAmount)}원
                    </p>
                  </div>
                )}
              </div>

              <Button
                onClick={() => navigate('/finance-connect')}
                className="max-w-[360px] h-[56px]"
              >
                계좌 연동으로 이동
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
