import { useState, useEffect } from 'react';
import { ProgressBar } from '@/shared/components';
import { Step1_Cohort } from '../components/Steps/Step1_Cohort';
import { Step2_Goal } from '../components/Steps/Step2_Goal';
import { Step3_Welcome } from '../components/Steps/Step3_Welcome';
import { submitOnboarding } from '../api/userApi';
import type { Cohort } from '@/shared/types';
import { useToast } from '@/shared/hooks';

export const OnboardingPage = () => {
  const [step, setStep] = useState(1);
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [onboardingData, setOnboardingData] = useState({
    cohortId: 0,
    goalAmount: 0,
  });
  const toast = useToast();

  useEffect(() => {
    const loadCohorts = async () => {
      // Prototyping: Using Mock Data
      const mockCohorts: Cohort[] = [
        { cohortId: 1, cohortCode: '14기' },
        { cohortId: 2, cohortCode: '15기' },
        { cohortId: 3, cohortCode: '16기' },
      ];

      setTimeout(() => {
        setCohorts(mockCohorts);
        setIsLoading(false);
      }, 500); // Simulate network delay
    };
    loadCohorts();
  }, []);

  const handleStep1Next = (cohortId: number) => {
    setOnboardingData((prev) => ({ ...prev, cohortId }));
    setStep(2);
  };

  const handleStep2Next = async (goalAmount: number) => {
    try {
      const finalData = { ...onboardingData, goalAmount };
      setOnboardingData(finalData);

      const response = await submitOnboarding(finalData);
      if (response.success) {
        setStep(3);
      }
    } catch (error) {
      console.error('Failed to submit onboarding:', error);
      toast.error('정보 저장에 실패했습니다. 다시 시도해주세요.');
    }
  };

  const progress = (step / 3) * 100;

  return (
    <div className="w-full max-w-[800px] mx-auto py-12 px-6">
      {step < 3 && (
        <div className="mb-16">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[14px] font-bold text-primary-blue">STEP {step}</span>
            <span className="text-[14px] font-bold text-gray-400">33% 완료</span>
          </div>
          <ProgressBar progress={progress} className="h-3 rounded-full" />
        </div>
      )}

      <div className="min-h-[500px] flex flex-col justify-center">
        {step === 1 && (
          <Step1_Cohort cohorts={cohorts} isLoading={isLoading} onNext={handleStep1Next} />
        )}
        {step === 2 && <Step2_Goal onNext={handleStep2Next} onBack={() => setStep(1)} />}
        {step === 3 && <Step3_Welcome />}
      </div>
    </div>
  );
};
