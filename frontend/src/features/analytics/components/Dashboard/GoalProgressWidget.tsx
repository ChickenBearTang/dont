import { Card, CircularProgress } from '@/shared/components';

export const GoalProgressWidget = () => {
  // Mock Data
  const goal = 1000000;
  const spent = 680000;
  const remaining = goal - spent;
  const progress = Math.round((spent / goal) * 100);

  return (
    <Card className="p-8 h-full flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow">
      <h3 className="text-gray-900 font-black text-[20px] mb-8">절약 목표 달성률</h3>

      <div className="relative w-48 h-48 mb-8">
        <CircularProgress
          size={192}
          strokeWidth={16}
          progress={progress}
          className="text-primary-blue"
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black text-gray-900">{Math.round((spent / goal) * 100)}%</span>
          <span className="text-[13px] text-gray-400 font-bold">달성 중</span>
        </div>
      </div>

      <div className="space-y-1 text-center">
        <p className="text-gray-400 text-[14px] font-medium">전체 목표: {goal.toLocaleString()}원</p>
        <p className="text-gray-500 font-bold mt-2">남은 금액</p>
        <p className="text-primary-blue text-2xl font-black tracking-tight">
          {remaining.toLocaleString()}원
        </p>
      </div>
    </Card>
  );
};
