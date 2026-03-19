import { useState } from 'react';
import type { Cohort } from '@/shared/types';
import { Button } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';

interface Step1Props {
  onNext: (cohortId: number) => void;
  cohorts: Cohort[];
  isLoading: boolean;
}

export const Step1_Cohort = ({ onNext, cohorts, isLoading }: Step1Props) => {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Mascot 
        src="/assets/mascot_happy.png"
        speech="반가워요! OOO님은 SSAFY 몇 기이신가요? 기수에 맞는 맞춤형 정보를 준비해드릴게요."
        className="mb-10"
      />

      <div className="w-full grid grid-cols-2 sm:grid-cols-3 gap-4 mb-10">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-[60px] bg-gray-100 animate-pulse rounded-2xl" />
          ))
        ) : (
          cohorts.map((cohort) => (
            <button
              key={cohort.cohortId}
              onClick={() => setSelectedId(cohort.cohortId)}
              className={`
                h-[60px] rounded-2xl font-bold text-[17px] transition-all
                ${selectedId === cohort.cohortId 
                  ? 'bg-primary-blue text-white shadow-lg shadow-blue-200 scale-[1.02]' 
                  : 'bg-white border-2 border-gray-100 text-gray-500 hover:border-blue-200'}
              `}
            >
              {cohort.cohortCode}
            </button>
          ))
        )}
      </div>

      <Button 
        disabled={selectedId === null}
        onClick={() => selectedId && onNext(selectedId)}
        className="max-w-[300px]"
      >
        다음 단계로
      </Button>
    </div>
  );
};
