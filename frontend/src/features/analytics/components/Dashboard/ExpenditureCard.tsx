import { Card } from '@/shared/components';
import { formatCurrency } from '@/shared/utils';

export const ExpenditureCard = () => {
  // Mock Data
  const spent = 452000;
  const lastMonth = 467000;
  const diff = lastMonth - spent;

  return (
    <Card className="p-8 h-full flex flex-col justify-between hover:shadow-md transition-shadow">
      <div>
        <h3 className="text-gray-500 font-bold text-[15px] mb-2">이번 달 지출</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-black text-gray-900">{formatCurrency(spent)}</span>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between bg-emerald-50 p-4 rounded-2xl border border-emerald-100">
        <div>
          <p className="text-emerald-700 text-[13px] font-bold">지난달보다</p>
          <p className="text-emerald-800 text-[16px] font-black">{formatCurrency(diff)} 아꼈어요!</p>
        </div>
        <div className="w-10 h-10 bg-emerald-500 text-white rounded-xl flex items-center justify-center text-xl">
          📉
        </div>
      </div>
    </Card>
  );
};
