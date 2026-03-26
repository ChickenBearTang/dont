import { useEffect, useState, useRef } from 'react';
import type { AxiosError } from 'axios';
import {
  getSpendingSummary,
  getMonthlyAiReport,
  generateMonthlyAiReport,
  sendAiJustification,
  regenerateAiReport,
} from '../api/reportApi';
import { useNavigate, useSearchParams } from 'react-router-dom';
import type {
  SpendingSummaryResponse,
  SpendingSummaryRank,
  AiReportPayload,
  CardRecommendationResponse,
} from '../types';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import mascotAnalyze from '@/assets/character/mascot_analyze.png';
import mascotJust from '@/assets/character/mascot_just.png';

const CATEGORY_COLORS = [
  '#3B82F6', // Blue
  '#8B5CF6', // Purple
  '#F59E0B', // Amber
  '#EC4899', // Pink
  '#10B981', // Emerald
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#F43F5E', // Rose
  '#84CC16', // Lime
  '#06B6D4', // Cyan
  '#9CA3AF', // Gray (fallback)
];

const formatToYYYYMMDD = (date: Date) => {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}${mm}${dd}`;
};

const formatToYYYYMM = (date: Date) => {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  return `${yyyy}-${mm}`;
};

const parseReportMonth = (reportMonth: string | null) => {
  if (!reportMonth || !/^\d{4}-\d{2}$/.test(reportMonth)) return null;

  const [yearText, monthText] = reportMonth.split('-');
  const year = Number(yearText);
  const month = Number(monthText);

  if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12) {
    return null;
  }

  return new Date(year, month - 1, 1);
};

const getMonthRange = (date: Date) => {
  const year = date.getFullYear();
  const month = date.getMonth();
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  return {
    startDate: formatToYYYYMMDD(firstDay),
    endDate: formatToYYYYMMDD(lastDay),
  };
};

const DonutChart = ({ data }: { data: SpendingSummaryRank[] }) => {
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  let strokeDashoffset = 0;

  return (
    <div className="relative w-44 h-44 lg:w-40 lg:h-40 mx-auto filter drop-shadow hover:drop-shadow-md transition-all">
      <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
        {data.length === 0 ? (
          <circle cx="50" cy="50" r={radius} fill="transparent" stroke="#F3F4F6" strokeWidth="16" />
        ) : (
          data.map((slice, i) => {
            const p = slice.percentage > 1 ? slice.percentage / 100 : slice.percentage;
            const sliceLength = p * circumference;
            const offset = strokeDashoffset;
            strokeDashoffset += sliceLength;
            return (
              <circle
                key={i}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={CATEGORY_COLORS[i % CATEGORY_COLORS.length]}
                strokeWidth="16"
                strokeDasharray={`${sliceLength} ${circumference}`}
                strokeDashoffset={-offset}
                className="transition-all duration-1000 ease-out hover:opacity-80 cursor-pointer hover:stroke-[18px]"
              />
            );
          })
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-[13px] font-bold text-gray-400">이달의 지출</span>
      </div>
    </div>
  );
};

const AIAnalysisCard = ({
  analysis,
  cardRecommendation,
  cardRecommendLoading,
  loading,
  isCurrentMonth,
  generating,
  onGenerate,
  onNavigateToRecommend,
}: {
  analysis: AiReportPayload['aiAnalysis'] | null;
  cardRecommendation: CardRecommendationResponse | null;
  cardRecommendLoading: boolean;
  loading: boolean;
  isCurrentMonth: boolean;
  generating: boolean;
  onGenerate: () => void;
  onNavigateToRecommend: () => void;
}) => {
  const { user } = useAuthStore();
  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-20 bg-gray-50/50 rounded-[32px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)] min-h-[450px]">
        <div className="w-8 h-8 border-4 border-gray-100 border-t-purple-500 rounded-full animate-spin mb-4" />
        <span className="text-[13px] font-semibold text-gray-500">
          AI가 소비 내역을 심층 분석하고 있습니다...
        </span>
      </div>
    );
  }

  if (!analysis) {
    if (isCurrentMonth) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-8 bg-gray-50/50 rounded-[32px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)] min-h-[450px]">
          <div className="bg-white p-4 rounded-[24px] shadow-sm text-center border border-gray-100">
            <img
              src={mascotAnalyze}
              alt="분석 중인 깐지"
              className="w-[280px] h-[280px] object-contain mx-auto -mb-4 animate-bounce"
              style={{ animationDuration: '2s' }}
            />
            <span className="text-[16px] font-bold text-gray-800 block mb-2 relative z-10">
              깐지가 열심히 모니터링 중이에요! 🐾
            </span>
            <span className="text-[14px] text-gray-500 mt-2 block leading-relaxed">
              이번 달 소비 내역이 모이면
              <br />
              리포트를 준비할게요.
            </span>
          </div>
        </div>
      );
    }

    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-8 bg-gray-50/50 rounded-[32px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)] min-h-[450px]">
        <div className="bg-white p-4 rounded-[24px] shadow-sm text-center max-w-sm w-full mx-4 border border-gray-100">
          <img
            src={mascotAnalyze}
            alt="리포트 준비 중인 깐지"
            className="w-[240px] h-[240px] object-contain mx-auto -mb-4 pt-2"
          />
          <span className="text-[16px] font-bold text-gray-800 block mb-2 relative z-10">
            {generating ? '리포트를 생성 중입니다...' : '아직 분석된 리포트가 없어요!'}
          </span>
          <span className="text-[13px] text-gray-500 mb-6 block leading-relaxed">
            AI가 {user?.nickname ? `${user.nickname}님` : '회원님'}의 소비 데이터를 분석하여
            <br />
            맞춤형 절약 솔루션을 알려드립니다.
          </span>
          <button
            onClick={onGenerate}
            disabled={generating}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3.5 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg active:scale-95"
          >
            {generating ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>분석 요청 중...</span>
              </>
            ) : (
              <>
                <span>✨</span> AI 분석 리포트 받아보기
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-gray-50/30 rounded-[32px] overflow-hidden flex flex-col min-h-[450px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
      <div className="bg-white px-5 pt-6 pb-4 rounded-t-[32px]">
        <h1 className="text-[20px] font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 tracking-[-0.02em] flex items-center gap-2">
          <span>✨</span> AI 심층 분석 리포트
        </h1>
        <p className="text-[13px] font-medium text-gray-400 mt-1">
          {user?.nickname ? `${user.nickname}님` : '회원님'}의 소비 패턴을 AI가 다각도로 분석하여 맞춤 솔루션을 제공합니다.
        </p>
      </div>

      <div className="flex-1 p-7 flex flex-col gap-6">

        {/* AI 기반 소비 유형 및 카드 추천 결과 */}
        {cardRecommendLoading ? (
          <div className="bg-white rounded-[24px] p-7 border border-gray-100 shadow-sm flex items-center justify-center min-h-[160px]">
            <div className="w-8 h-8 border-4 border-gray-100 border-t-purple-500 rounded-full animate-spin"></div>
          </div>
        ) : cardRecommendation && cardRecommendation.user_persona ? (
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-[24px] p-7 border border-indigo-100 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <div className="text-4xl text-indigo-500">🧑‍💻</div>
              <div>
                <h3 className="text-[14px] font-bold text-indigo-500 tracking-tight">AI 분석 맞춤 소비 유형</h3>
                <div className="text-[20px] font-black text-gray-900">{cardRecommendation.user_persona.name}</div>
              </div>
            </div>
            <p className="text-[14px] text-gray-700 leading-relaxed font-medium mb-6">
              {cardRecommendation.user_persona.description}
            </p>

            {cardRecommendation.best_card && (
              <div className="bg-white rounded-2xl p-5 border border-indigo-100/50 shadow-[0_2px_8px_rgba(79,70,229,0.06)]">
                <div className="flex justify-between items-start mb-2">
                  <span className="bg-indigo-100 text-indigo-700 text-[11px] font-bold px-2.5 py-1 rounded-full">Best 추천 카드</span>
                </div>
                <div className="flex justify-between items-center flex-wrap gap-4">
                  <div>
                    <h4 className="text-[18px] font-extrabold text-gray-900">{cardRecommendation.best_card.name}</h4>
                    <p className="text-[13px] text-gray-500 font-medium mt-1">{cardRecommendation.best_card.main_text}</p>
                  </div>
                  <div className="text-right ml-auto">
                    <div className="text-[12px] text-indigo-400 font-bold mb-1">예상 월 혜택</div>
                    <div className="flex items-baseline justify-end">
                      <span className="text-[22px] font-black tracking-tighter text-indigo-600">{cardRecommendation.best_card.estimated_savings?.toLocaleString()}</span>
                      <span className="text-[14px] font-bold text-indigo-600 ml-1">원</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={onNavigateToRecommend}
              className="w-full mt-4 bg-white hover:bg-indigo-50 text-indigo-600 border border-indigo-200 font-bold py-3.5 rounded-xl transition-all shadow-sm active:scale-[0.98] flex items-center justify-center gap-2"
            >
              맞춤 카드 추천 전체 결과 확인하기 <span className="text-[18px]">›</span>
            </button>
          </div>
        ) : null}

        <div className="bg-white rounded-[24px] p-7 border border-gray-100 shadow-sm transition-shadow hover:shadow-md">
          <h3 className="text-[18px] font-extrabold text-gray-900 mb-5 flex items-center gap-2">
            <span className="text-xl">📊</span>
            <span>이달의 소비 패턴</span>
          </h3>
          <div className="flex flex-col gap-3">
            {analysis.consumption_patterns?.map((text: string, idx: number) => (
              <div key={idx} className="flex gap-3 text-[14px] text-gray-700 font-medium">
                <span className="text-blue-500 font-bold shrink-0 mt-0.5">•</span>
                <p className="leading-relaxed">{text}</p>
              </div>
            ))}
            {(!analysis.consumption_patterns || analysis.consumption_patterns.length === 0) && (
              <p className="text-[14px] text-gray-400 font-medium pb-2">
                기록된 소비 패턴이 없습니다.
              </p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-purple-100 shadow-sm transition-shadow hover:shadow-md ring-1 ring-purple-50">
          <h3 className="text-[16px] font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600 mb-3 flex items-center gap-2">
            <span className="text-lg">💡</span>
            <span>AI 맞춤 솔루션</span>
          </h3>
          <div className="flex flex-col gap-3">
            {analysis.actionable_solutions?.map((text: string, idx: number) => (
              <div
                key={idx}
                className="flex gap-3 text-[13px] text-gray-800 font-semibold bg-gradient-to-br from-purple-50 to-blue-50 p-4 rounded-xl border border-blue-100/30"
              >
                <span className="text-blue-500 text-[15px] shrink-0 mt-0.5">✅</span>
                <p className="leading-relaxed">{text}</p>
              </div>
            ))}
            {(!analysis.actionable_solutions || analysis.actionable_solutions.length === 0) && (
              <p className="text-[14px] text-gray-400 font-medium pb-2">
                제안할 솔루션이 없습니다.
              </p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm transition-shadow hover:shadow-md">
          <h3 className="text-[16px] font-extrabold text-gray-900 mb-3 flex items-center gap-2">
            <span className="text-lg">🔍</span>
            <span>소비 특이사항</span>
          </h3>
          <div className="flex flex-col gap-3">
            {analysis.anomaly_explanations?.map((text: string, idx: number) => (
              <div key={idx} className="flex gap-3 text-[14px] text-gray-700 font-medium">
                <span className="text-orange-400 font-bold shrink-0 mt-0.5">•</span>
                <p className="leading-relaxed">{text}</p>
              </div>
            ))}
            {(!analysis.anomaly_explanations || analysis.anomaly_explanations.length === 0) && (
              <p className="text-[14px] text-gray-400 font-medium pb-2">
                발견된 특이사항이 없습니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const ReportChatbot = ({
  targetMonth,
  onRegenerate,
  onApplyRegeneratedReport,
}: {
  targetMonth: string;
  onRegenerate: () => void;
  onApplyRegeneratedReport: (payload?: AiReportPayload) => void;
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ sender: 'user' | 'ai'; text: string }[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [isValidated, setIsValidated] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const handleSend = async () => {
    if (!inputText.trim() || loading) return;
    const msg = inputText;
    setMessages((prev) => [...prev, { sender: 'user', text: msg }]);
    setInputText('');
    setLoading(true);
    setIsValidated(false);

    try {
      const res = await sendAiJustification(targetMonth, msg);
      const resData = (
        res as { data?: { data?: Record<string, unknown> } | Record<string, unknown> }
      )?.data;
      const data = (resData && 'data' in resData && resData.data ? resData.data : resData) as
        | Record<string, unknown>
        | undefined;

      const aiResponse = String(
        data?.ai_response ?? data?.aiResponse ?? '설득력이 있는 내용이네요. 내용을 검토하겠습니다.'
      );
      const valid = Boolean(data?.is_valid ?? data?.valid ?? false);
      const reportRegenerated = Boolean(
        data?.report_regenerated ?? data?.reportRegenerated ?? false
      );
      const regeneratedReport = (
        data?.regenerated_report ?? data?.regeneratedReport
      ) as { reportPayload?: AiReportPayload } | undefined;

      setMessages((prev) => [...prev, { sender: 'ai', text: aiResponse }]);

      if (reportRegenerated) {
        onApplyRegeneratedReport(regeneratedReport?.reportPayload);
        setMessages((prev) => [
          ...prev,
          { sender: 'ai', text: '소명 내용을 반영해서 소비리포트도 바로 업데이트했어요.' },
        ]);
        setIsValidated(false);
      } else if (valid) {
        setIsValidated(true);
      }
    } catch (e) {
      console.error(e);
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', text: '오류가 발생했습니다. 잠시 후 다시 시도해주세요.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    if (regenerating) return;
    setRegenerating(true);
    try {
      await onRegenerate();
      setMessages((prev) => [
        ...prev,
        { sender: 'ai', text: '방금 전달해주신 의견을 바탕으로 새로운 리포트를 작성했습니다! 😊' },
      ]);
      setIsValidated(false);
    } catch (e) {
      console.error(e);
      alert('리포트 재작성에 실패했습니다.');
    } finally {
      setRegenerating(false);
    }
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-8 right-8 flex flex-col items-end z-50 pointer-events-none">
        <div
          className={`mb-2 mr-2 flex flex-col items-end transition-all duration-500 ease-out z-50 ${isHovered
              ? 'opacity-100 translate-y-0 scale-100'
              : 'opacity-0 translate-y-4 scale-90 pointer-events-none'
            }`}
        >
          <div className="bg-white px-4 py-2.5 rounded-2xl shadow-xl border border-gray-100 text-[13px] font-black text-eel mb-2 relative pointer-events-auto">
            리포트에 대해 불만이 있냐루?
            <div className="absolute -bottom-1 right-6 w-2.5 h-2.5 bg-white border-r border-b border-gray-100 rotate-45" />
          </div>
          <img
            src={mascotJust}
            alt="질문하는 깐지"
            className={`w-24 h-24 object-contain pointer-events-auto transition-transform duration-700 ${isHovered ? '-rotate-[30deg]' : 'rotate-0'
              } origin-bottom-right`}
          />
        </div>
        <button
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onClick={() => {
            setIsOpen(true);
            setIsHovered(false);
          }}
          className="w-16 h-16 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full shadow-lg hover:shadow-xl hover:scale-110 transition-all flex items-center justify-center text-white text-3xl ring-4 ring-purple-100 animate-bounce pointer-events-auto"
          aria-label="AI 반박하기"
        >
          💬
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-8 right-8 w-80 bg-white rounded-[24px] shadow-2xl border border-gray-100 flex flex-col overflow-hidden z-50 ring-4 ring-purple-100/50">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4 text-white flex justify-between items-center shadow-md z-10">
        <div className="font-bold flex items-center gap-2">
          <span className="text-xl">🤖</span> AI에게 반박하기
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-white/80 hover:text-white text-2xl leading-none"
        >
          &times;
        </button>
      </div>

      <div className="h-96 p-4 overflow-y-auto bg-gray-50 flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="text-center mt-10">
            <div className="bg-blue-100 text-blue-800 p-4 rounded-2xl rounded-tr-sm text-sm border-blue-200 inline-block text-left shadow-sm">
              <p className="font-bold mb-1">이번 달 분석 결과가 억울하신가요?</p>
              <p>
                AI에게 그 이유를 설명하고 리포트를 수정해 보세요! (예: "병원비는 어쩔 수 없는
                고정지출이야")
              </p>
            </div>
          </div>
        )}

        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`max-w-[85%] rounded-2xl p-3 text-[14px] leading-relaxed shadow-sm ${m.sender === 'user'
                ? 'bg-blue-600 text-white self-end rounded-tr-sm'
                : 'bg-white text-gray-800 self-start rounded-tl-sm border border-gray-100'
              }`}
          >
            {m.text}
          </div>
        ))}

        {loading && (
          <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm p-3 self-start text-gray-500 flex gap-1 w-14 items-center justify-center h-10">
            <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            <div
              className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.1s' }}
            />
            <div
              className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.2s' }}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-white border-t border-gray-100 flex flex-col gap-3 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10">
        {isValidated && (
          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="w-full bg-gradient-to-br from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-3 px-4 rounded-xl shadow-md transition-all active:scale-95 text-[14px] flex items-center justify-center gap-2"
          >
            {regenerating ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>재작성 중...</span>
              </>
            ) : (
              <>
                <span>✨</span> 의견 반영해서 리포트 재작성하기!
              </>
            )}
          </button>
        )}
        <div className="flex gap-2">
          <input
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="억울한 이유를 입력해주세요..."
            className="flex-1 bg-gray-100 rounded-xl px-4 py-3 text-[14px] outline-none border border-transparent focus:border-purple-300 focus:bg-white transition-all shadow-inner"
          />
          <button
            onClick={handleSend}
            disabled={loading || !inputText.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-4 font-bold disabled:opacity-50 transition-all active:scale-95 shadow-md flex items-center justify-center disabled:active:scale-100"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-5 h-5 -mr-1"
            >
              <path d="M3.478 2.404a.75.75 0 00-.926.941l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.404z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export const MonthlyReportPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuthStore();

  const getNormalizedMonthDate = (date: Date) =>
    new Date(date.getFullYear(), date.getMonth(), 1);

  const [currentDate, setCurrentDate] = useState(() => {
    const requestedDate = parseReportMonth(searchParams.get('reportMonth'));
    return getNormalizedMonthDate(requestedDate ?? new Date());
  });

  const [summary, setSummary] = useState<SpendingSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  const [aiAnalysis, setAiAnalysis] = useState<AiReportPayload['aiAnalysis'] | null>(null);
  const [aiLoading, setAiLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const [cardRecommendation, setCardRecommendation] =
    useState<CardRecommendationResponse | null>(null);
  const [cardRecommendLoading, setCardRecommendLoading] = useState(true);

  const extractReportPayload = (res: unknown): AiReportPayload | undefined =>
    (res as { data?: { data?: { reportPayload?: AiReportPayload } } })?.data?.data?.reportPayload ||
    (res as { data?: { reportPayload?: AiReportPayload } })?.data?.reportPayload ||
    (res as { reportPayload?: AiReportPayload })?.reportPayload;

  const getAxiosStatus = (error: unknown): number | undefined =>
    (error as AxiosError | undefined)?.response?.status;

  const applyMonthlyReportPayload = (payload?: AiReportPayload) => {
    setAiAnalysis(payload?.aiAnalysis ?? null);
    setCardRecommendation(payload?.cardRecommendation ?? null);
  };

  const isCurrentMonth =
    currentDate.getMonth() === new Date().getMonth() &&
    currentDate.getFullYear() === new Date().getFullYear();

  const isLastMonth = (() => {
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    return (
      currentDate.getFullYear() === lastMonth.getFullYear() &&
      currentDate.getMonth() === lastMonth.getMonth()
    );
  })();

    const handleGenerateReport = async () => {
    try {
      setGenerating(true);
      const reportMonth = formatToYYYYMM(currentDate);
      await generateMonthlyAiReport(reportMonth);

      setAiLoading(true);
      setCardRecommendLoading(true);
      const res = await getMonthlyAiReport(reportMonth);
      applyMonthlyReportPayload(extractReportPayload(res));
    } catch (error) {
      console.error('Failed to generate AI report:', error);
      alert('리포트 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setGenerating(false);
      setAiLoading(false);
      setCardRecommendLoading(false);
    }
  };

  const handleChatRegenerate = async () => {
    try {
      const reportMonth = formatToYYYYMM(currentDate);
      await regenerateAiReport(reportMonth);

      setAiLoading(true);
      setCardRecommendLoading(true);
      const res = await getMonthlyAiReport(reportMonth);
      applyMonthlyReportPayload(extractReportPayload(res));
    } catch (error) {
      console.error(error);
      throw error;
    } finally {
      setAiLoading(false);
      setCardRecommendLoading(false);
    }
  };

  useEffect(() => {
    const requestedDate = parseReportMonth(searchParams.get('reportMonth'));

    if (!requestedDate) return;

    const normalizedRequested = getNormalizedMonthDate(requestedDate);

    if (formatToYYYYMM(normalizedRequested) !== formatToYYYYMM(currentDate)) {
      setCurrentDate(normalizedRequested);
    }
  }, [searchParams]);

  useEffect(() => {
    const normalizedCurrent = getNormalizedMonthDate(currentDate);
    const currentParam = searchParams.get('reportMonth');
    const nextMonth = formatToYYYYMM(normalizedCurrent);

    if (currentParam === nextMonth) return;

    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('reportMonth', nextMonth);
    setSearchParams(nextParams, { replace: true });
  }, [currentDate, searchParams, setSearchParams]);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setSummaryLoading(true);
        const { startDate, endDate } = getMonthRange(currentDate);
        const res = await getSpendingSummary(startDate, endDate);

        let rankList = res.rankColumList || [];
        rankList = [...rankList].sort((a, b) => b.percentage - a.percentage);

        setSummary({
          ...res,
          rankColumList: rankList,
        });
      } catch (error) {
        console.error('Failed to fetch spending summary:', error);
        setSummary(null);
      } finally {
        setSummaryLoading(false);
      }
    };

    const fetchAiReport = async () => {
      try {
        setAiLoading(true);
        setCardRecommendLoading(true);
        const reportMonth = formatToYYYYMM(currentDate);
        const res = await getMonthlyAiReport(reportMonth);
        applyMonthlyReportPayload(extractReportPayload(res));
      } catch (error) {
        if (getAxiosStatus(error) !== 404) {
          console.error('Failed to fetch AI report:', error);
        }
        setAiAnalysis(null);
        setCardRecommendation(null);
      } finally {
        setAiLoading(false);
        setCardRecommendLoading(false);
      }
    };

    fetchSummary();
    fetchAiReport();
  }, [currentDate]);

  const handlePrevMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  return (
    <div className="w-full max-w-[1280px] mx-auto min-h-screen px-4 py-4 pb-16">
      <button
        onClick={() => navigate('/finance')}
        className="flex items-center gap-2 text-gray-400 hover:text-gray-800 font-bold mb-4 ml-4 transition-colors"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        금융 홈으로
      </button>

      <div className="flex items-center justify-between w-full max-w-[260px] mx-auto bg-white/80 p-1.5 mb-6 rounded-2xl shadow-sm border border-gray-100/80 backdrop-blur-sm">
        <button
          onClick={handlePrevMonth}
          className="p-2.5 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-800 transition active:scale-95"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="text-center font-black text-gray-900 text-[18px] tracking-tight">
          {currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월
        </div>

        <button
          onClick={handleNextMonth}
          disabled={
            currentDate.getMonth() === new Date().getMonth() &&
            currentDate.getFullYear() === new Date().getFullYear()
          }
          className="p-2.5 rounded-xl text-gray-400 hover:bg-gray-50 hover:text-gray-800 transition disabled:opacity-20 disabled:hover:bg-transparent disabled:active:scale-100 active:scale-95"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        <div className="w-full bg-gray-50/30 rounded-[32px] overflow-hidden flex flex-col min-h-[450px] border border-gray-100/80 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="bg-white px-5 pt-6 pb-4 rounded-t-[32px]">
            <h1 className="text-[20px] font-bold text-gray-900 tracking-[-0.02em] flex items-center gap-2">
              <span>💳</span> 이달의 소비 리포트
            </h1>
            <p className="text-[13px] font-medium text-gray-400 mt-1">
              {user?.nickname ? `${user.nickname}님` : '회원님'}의 카테고리별 주요 소비패턴을 분석합니다.
            </p>
          </div>

          <div className="flex-1 p-5 flex flex-col">
            {summaryLoading ? (
              <div className="flex-1 flex flex-col items-center justify-center text-gray-400 py-10">
                <div className="w-8 h-8 border-4 border-gray-100 border-t-blue-600 rounded-full animate-spin mb-4" />
                <span className="text-[13px] font-semibold">리포트를 분석 중입니다...</span>
              </div>
            ) : summary ? (
              <div className="flex flex-col gap-4">
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex flex-col items-center">
                  <h3 className="text-[15px] font-extrabold text-gray-900 mb-6 w-full text-center tracking-tight">
                    전체 소비 요약
                  </h3>

                  <DonutChart data={summary.rankColumList} />

                  <div className="mt-4 text-center flex flex-col items-center">
                    <p className="text-[13px] text-gray-400 font-bold mb-1 tracking-tight">
                      총 이용 금액
                    </p>
                    <div className="flex items-baseline justify-center">
                      <span className="text-[28px] font-black tracking-tighter text-blue-600">
                        {summary.totalAmount?.toLocaleString() || 0}
                      </span>
                      <span className="text-[16px] font-bold text-gray-800 ml-1">원</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                  <h3 className="text-[15px] font-extrabold text-gray-900 mb-4 tracking-tight">
                    어디에 가장 많이 썼을까요?
                  </h3>

                  {summary.rankColumList.length === 0 ? (
                    <div className="py-12 text-center text-[14px] font-bold text-gray-400 bg-gray-50 rounded-2xl">
                      해당 월의 결제 내역이 없습니다.
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      {summary.rankColumList.map((rank, idx) => {
                        const p = rank.percentage > 1 ? rank.percentage / 100 : rank.percentage;
                        const displayPercent = (p * 100).toFixed(1);

                        return (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-2xl hover:border-blue-100 hover:shadow-sm transition-all group cursor-pointer"
                          >
                            <div className="flex items-center gap-3">
                              <div
                                className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-inner"
                                style={{
                                  backgroundColor: `${CATEGORY_COLORS[idx % CATEGORY_COLORS.length]}15`,
                                }}
                              >
                                <span
                                  className="text-[13px] font-black group-hover:scale-110 transition-transform"
                                  style={{ color: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                                >
                                  {idx + 1}위
                                </span>
                              </div>

                              <div>
                                <div className="text-[15px] font-extrabold text-gray-800 mb-0.5">
                                  {rank.categoryName}
                                </div>
                                <div className="text-[11px] font-bold text-gray-400">
                                  전체 지출의 {displayPercent}% 차지
                                </div>
                              </div>
                            </div>

                            <div className="text-right">
                              <div className="text-[16px] font-black tracking-tight text-gray-900 group-hover:text-blue-600 transition-colors">
                                {rank.amount?.toLocaleString() || 0}원
                              </div>
                              {rank.amount_prv > 0 && (
                                <div className="text-[12px] font-semibold text-gray-400 mt-1">
                                  저번 달보다 {((rank.amount / rank.amount_prv) * 100).toFixed(0)}%
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-400 bg-white rounded-[24px] border border-gray-100 shadow-sm py-20">
                데이터를 불러올 수 없습니다.
              </div>
            )}
          </div>
        </div>

        <AIAnalysisCard
          analysis={aiAnalysis}
          cardRecommendation={cardRecommendation}
          cardRecommendLoading={cardRecommendLoading}
          loading={aiLoading}
          isCurrentMonth={isCurrentMonth}
          generating={generating}
          onGenerate={handleGenerateReport}
          onNavigateToRecommend={() =>
            navigate(`/finance/cards/recommendation?month=${formatToYYYYMM(currentDate)}`)
          }
        />
      </div>

      {isLastMonth && aiAnalysis && (
        <ReportChatbot
          targetMonth={formatToYYYYMM(currentDate)}
          onRegenerate={handleChatRegenerate}
          onApplyRegeneratedReport={applyMonthlyReportPayload}
        />
      )}
    </div>
  );
};
