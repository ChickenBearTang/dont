import { useState } from 'react';
import { Button, Input } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';
import { formatNumber } from '@/shared/utils';

interface Step2Props {
  onNext: (amount: number) => void;
  onBack: () => void;
}

export const Step2_Goal = ({ onNext, onBack }: Step2Props) => {
  const [amount, setAmount] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9]/g, '');
    setAmount(value);
  };

  const isValid = Number(amount) >= 10000;

  return (
    <div className="flex flex-col items-center animate-in fade-in slide-in-from-right-4 duration-500">
      <Mascot
        src="/assets/mascot_happy.png"
        speech="멋져요! 이제 한 달 동안 얼마나 아끼고 싶으신지 목표 금액을 알려주세요."
        className="mb-10"
      />

      <div className="w-full max-w-[400px] mb-10">
        <Input
          label="절약 목표 금액"
          placeholder="예: 300,000"
          value={amount ? formatNumber(Number(amount)) : ''}
          onChange={handleInputChange}
          unit="원"
        />
        <p className="mt-4 text-[13px] text-gray-400 font-medium text-center">
          * 최소 10,000원부터 설정 가능합니다.
        </p>
      </div>

      <div className="flex gap-4 w-full max-w-[400px]">
        <Button variant="outline" onClick={onBack}>
          이전
        </Button>
        <Button disabled={!isValid} onClick={() => onNext(Number(amount))}>
          설정 완료
        </Button>
      </div>
    </div>
  );
};
