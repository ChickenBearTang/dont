const ExpenditureCard = () => (
  <Card className="p-8 flex flex-col h-full hover:shadow-md transition-shadow">
    <h3 className="text-gray-900 font-black text-[20px] mb-4">이번 달 지출 현황</h3>
    <div className="flex-1 flex flex-col items-center justify-center">
      <div className="text-4xl font-black text-gray-800 mb-2">₩ 450,000</div>
      <p className="text-gray-400 font-medium text-sm">목표 예산의 45% 사용</p>
    </div>
  </Card>
);

const GoalProgressWidget = () => (
  <Card className="p-8 flex flex-col h-full hover:shadow-md transition-shadow">
    <h3 className="text-gray-900 font-black text-[20px] mb-4">저축 목표 달성률</h3>
    <div className="flex-1 flex flex-col items-center justify-center">
      <div className="w-full bg-gray-100 rounded-full h-4 mb-4 overflow-hidden">
        <div className="bg-blue-600 h-4 rounded-full" style={{ width: '60%' }}></div>
      </div>
      <p className="text-gray-500 font-semibold">맥북 프로 구매 (60%)</p>
    </div>
  </Card>
);
import { Card } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';

export const DashboardPage = () => {
  return (
    <div className="space-y-10">
      <section className="flex flex-col md:flex-row items-center justify-between gap-8 bg-white p-10 rounded-[40px] border border-gray-100 shadow-sm">
        <div className="space-y-4 text-center md:text-left">
          <h2 className="text-3xl font-black text-gray-900 leading-tight">
            안녕하세요,{' '}
            <span className="text-primary-blue underline underline-offset-8">김싸피</span>님!
            <br />
            오늘도 현명한 소비 중이시네요.
          </h2>
          <p className="text-gray-500 font-medium text-lg italic">
            "작은 아낌이 모여 당신의 큰 꿈을 만듭니다."
          </p>
        </div>
        <Mascot
          src="/assets/mascot_happy.png"
          speech="벌써 목표의 60%를 넘으셨어요! 대단해요!"
          className="w-full max-w-[300px]"
        />
      </section>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <ExpenditureCard />
        </div>

        <div className="lg:col-span-1">
          <GoalProgressWidget />
        </div>

        <Card className="lg:col-span-1 p-8 flex flex-col hover:shadow-md transition-shadow">
          <h3 className="text-gray-900 font-black text-[20px] mb-6">최근 알림</h3>
          <div className="space-y-4">
            {[
              {
                id: 1,
                title: '커피 값 4,500원 절약!',
                desc: '오늘의 무지출 챌린지 성공!',
                time: '방금 전',
                icon: '☕',
              },
              {
                id: 2,
                title: '식비 예산 주의',
                desc: '목표 예산의 80%를 사용했어요.',
                time: '2시간 전',
                icon: '⚠️',
              },
              {
                id: 3,
                title: '포인트 적립 완료',
                desc: '어제 절약 보상 500P가 입금되었습니다.',
                time: '어제',
                icon: '💰',
              },
            ].map((item) => (
              <div
                key={item.id}
                className="flex gap-4 p-4 rounded-2xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100"
              >
                <div className="w-12 h-12 bg-white shadow-sm border border-gray-50 rounded-xl flex items-center justify-center text-2xl">
                  {item.icon}
                </div>
                <div className="flex-1">
                  <p className="text-[15px] font-bold text-gray-900">{item.title}</p>
                  <p className="text-[13px] text-gray-500 font-medium">{item.desc}</p>
                  <p className="text-[11px] text-gray-400 mt-1">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <section className="bg-[#F1F5F9] p-10 rounded-[40px] border border-gray-200 border-dashed">
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-black text-gray-400">카테고리별 상세 분석</h3>
          <p className="text-gray-400 font-medium">
            데이터 분석 기능은 현재 준비 중입니다. 곧 만나보실 수 있어요!
          </p>
        </div>
      </section>
    </div>
  );
};
