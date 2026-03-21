import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProgressBar } from '@/shared/components';
import { Step2_Goal } from '../components/Steps/Step2_Goal';
import { Step3_Welcome } from '../components/Steps/Step3_Welcome';
import { fetchOnboardingStatus, submitOnboarding } from '../api/userApi';
import { useToast } from '@/shared/hooks';

export const OnboardingPage = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [onboardingData, setOnboardingData] = useState({
    goalAmount: 0,
  });
  const toast = useToast();

  useEffect(() => {
    const loadOnboardingStatus = async () => {
      try {
        const statusResponse = await fetchOnboardingStatus();

        if (statusResponse.data.onboardingCompleted) {
          navigate('/finance-connect', { replace: true });
          return;
        }
      } catch (error) {
        console.error('Failed to load onboarding data:', error);
        toast.error('온보딩 정보를 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };
    loadOnboardingStatus();
  }, [navigate, toast]);

  const handleStep2Next = async (goalAmount: number) => {
    try {
      const finalData = { ...onboardingData, goalAmount };
      setOnboardingData(finalData);

      const response = await submitOnboarding(finalData);
      if (response.success && response.data.onboardingCompleted) {
        setStep(3);
      }
    } catch (error) {
      console.error('Failed to submit onboarding:', error);
      toast.error('정보 저장에 실패했습니다. 다시 시도해주세요.');
    }
  };

  const progress = (step / 2) * 100;

  if (isLoading) {
    return (
      <div className="w-full max-w-[800px] mx-auto py-12 px-6">
        <div className="min-h-[500px] flex items-center justify-center text-gray-400 font-semibold">
          온보딩 정보를 불러오는 중입니다...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[800px] mx-auto py-12 px-6">
      {step < 2 && (
        <div className="mb-16">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[14px] font-bold text-primary-blue">STEP {step}</span>
            <span className="text-[14px] font-bold text-gray-400">
              {Math.round(progress)}% 완료
            </span>
          </div>
          <ProgressBar progress={progress} className="h-3 rounded-full" />
        </div>
      )}

      <div className="min-h-[500px] flex flex-col justify-center">
        {step === 1 && <Step2_Goal onNext={handleStep2Next} onBack={() => navigate(-1)} />}
        {step === 2 && <Step3_Welcome />}
      </div>
    </div>
  );
};
