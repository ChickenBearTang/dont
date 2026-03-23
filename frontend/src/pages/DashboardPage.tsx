// Temporary Mock Components
import { Card } from '@/shared/components';
import { Mascot } from '@/shared/components/Mascot';

const ExpenditureCard = () => (
  <Card className="p-8 flex flex-col h-full h-full">
    <h3 className="text-eel font-black text-[20px] tracking-tight mb-4">이번 달 지출 현황</h3>
    <div className="flex-1 flex flex-col items-center justify-center">
      <div className="text-4xl font-black text-eel mb-2 tracking-tighter">₩ 450,000</div>
      <p className="text-text-muted font-bold text-sm">목표 예산의 45% 사용</p>
    </div>
  </Card>
);

const GoalProgressWidget = () => (
  <Card className="p-8 flex flex-col h-full">
    <h3 className="text-eel font-black text-[20px] tracking-tight mb-4">저축 목표 달성률</h3>
    <div className="flex-1 flex flex-col items-center justify-center w-full px-2">
      <div className="w-full bg-surface-soft rounded-full h-[18px] mb-5 overflow-hidden shadow-inner">
        <div
          className="bg-gradient-to-r from-primary-blue to-accent h-full rounded-full transition-all duration-1000"
          style={{ width: '60%' }}
        ></div>
      </div>
      <p className="text-text-strong font-bold tracking-tight">맥북 프로 구매 (60%)</p>
    </div>
  </Card>
);

export const DashboardPage = () => {
  return (
    <div className="space-y-10 max-w-[1200px] mx-auto pb-10">
      {/* 상단 환영 영역 - 이제 공통 Card 블록을 사용합니다 */}
      <Card className="flex flex-col md:flex-row items-center justify-between gap-8 !p-10 lg:!p-12 !rounded-[36px]">
        <div className="space-y-4 text-center md:text-left z-10 relative">
          <h2 className="text-[2rem] lg:text-[2.5rem] font-black text-eel leading-[1.3] tracking-tight">
            안녕하세요,{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-blue to-accent drop-shadow-sm">
              김싸피
            </span>
            님!
            <br />
            오늘도 현명한 소비 중이시네요.
          </h2>
          <p className="text-text-muted font-bold text-lg">
            "작은 아낌이 모여 당신의 큰 꿈을 만듭니다."
          </p>
        </div>
        <Mascot
          src="/assets/mascot_happy.png"
          speech="벌써 목표의 60%를 넘으셨어요! 대단해요!"
          className="w-full max-w-[320px] z-10 hover:scale-105 transition-transform duration-500"
        />
      </Card>

      {/* 메인 위젯 그리드 */}
      <div className="grid lg:grid-cols-3 gap-8">
        {/* 지출 카드 */}
        <div className="lg:col-span-1">
          <ExpenditureCard />
        </div>

        {/* 목표 달성 위젯 */}
        <div className="lg:col-span-1">
          <GoalProgressWidget />
        </div>

        {/* 최근 알림/활동 (Mock) */}
        <Card className="lg:col-span-1 p-8 flex flex-col">
          <h3 className="text-eel font-black text-[20px] tracking-tight mb-6">최근 알림</h3>
          <div className="space-y-4">
            {[
              {
                id: 1,
                title: '커피 값 4,500원 절약!',
                desc: '오늘의 무지출 챌린지 성공!',
                time: '방금 전',
                icon: '☕',
                bgColor: 'bg-orange-50',
              },
              {
                id: 2,
                title: '식비 예산 주의',
                desc: '목표 예산의 80%를 사용했어요.',
                time: '2시간 전',
                icon: '⚠️',
                bgColor: 'bg-red-50',
              },
              {
                id: 3,
                title: '포인트 적립 완료',
                desc: '어제 절약 보상 500P가 입금되었습니다.',
                time: '어제',
                icon: '💰',
                bgColor: 'bg-blue-50',
              },
            ].map((item) => (
              <div
                key={item.id}
                className="flex gap-4 p-4 rounded-[20px] hover:bg-white/80 transition-colors border border-transparent hover:border-white/90 shadow-sm hover:shadow-md cursor-pointer group"
              >
                <div
                  className={`w-[52px] h-[52px] ${item.bgColor} shadow-sm border border-white/50 rounded-2xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform`}
                >
                  {item.icon}
                </div>
                <div className="flex-1 overflow-hidden">
                  <p className="text-[15px] font-black text-eel truncate tracking-tight">
                    {item.title}
                  </p>
                  <p className="text-[13px] text-text-muted font-bold truncate mt-0.5">
                    {item.desc}
                  </p>
                  <p className="text-[11px] text-text-subtle font-semibold mt-1.5">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 하단 상세 차트 섹션 (Placeholder) */}
      <Card className="!bg-surface-soft/40 p-12 !rounded-[36px] border border-line-soft border-dashed flex items-center justify-center min-h-[200px] shadow-none hover:shadow-none hover:translate-y-0">
        <div className="text-center space-y-3 opacity-70">
          <h3 className="text-2xl font-black text-text-muted tracking-tight">
            카테고리별 상세 분석
          </h3>
          <p className="text-text-subtle font-bold">
            데이터 분석 기능은 현재 준비 중입니다. 곧 만나보실 수 있어요!
          </p>
        </div>
      </Card>
    </div>
  );
};
