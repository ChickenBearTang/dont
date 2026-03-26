import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { getCardRecommendation } from '@/features/finance/report/api/reportApi';
import type { CardRecommendationResponse, CardResult } from '@/features/finance/report/types';
import { getMyCards, getCardTransactions } from '../api/cardApi';
import type { TransactionItemDto } from '../types';

type BenefitLine = {
  targetType: string;
  rate: number;
  typeLabel: string;
  spentAmount: number;
  estimatedDiscount: number;
  merchants: { name: string; amount: number }[];
};

const TYPE_LABELS: Record<string, string> = {
  P01: '배달/식사',
  P02: '편의점',
  P03: '고정비',
  P04: '구독/OTT',
  P05: '교통/택시',
  P06: '생활/뷰티',
  P07: '카페',
  P08: '쇼핑',
  P09: '교육/도서',
  P10: '마트/장보기',
  P11: '여행',
  P12: '오프라인 쇼핑',
  P13: '문화/여가',
};

const CATEGORY_TO_TYPE: Record<string, string> = {
  식사_음식: 'P01',
  편의점_마트: 'P02',
  카페_디저트: 'P07',
  의료_건강: 'P06',
  문화_여가: 'P13',
};

const STORE_KEYWORDS: Record<string, string[]> = {
  P01: ['배달의민족', '쿠팡이츠', '요기요', '배민'],
  P02: ['CU', 'GS25', '세븐일레븐', '이마트24', '편의점'],
  P03: ['월세', '보험', '통신비', 'SKT', 'KT', 'LGU+', '수도광열'],
  P04: ['넷플릭스', '유튜브', '디즈니', '티빙', 'OTT'],
  P05: ['카카오T', '택시', '우티', 'TADA'],
  P06: ['올리브영', '다이소', '롭스'],
  P07: ['스타벅스', '투썸', '메가커피', '컴포즈', '이디야', '카페'],
  P08: ['무신사', '지그재그', '29CM', '백화점'],
  P09: ['인프런', '패스트캠퍼스', '서점', '교보문고'],
  P10: ['이마트', '홈플러스', '롯데마트', '식자재', '정육'],
  P11: ['항공', '비행기', '철도', 'KTX', 'SRT', '기차', '아고다', '호텔', '숙박', '에어비앤비', '면세점'],
  P12: ['백화점', '현대백화점', '롯데백화점', '신세계', '아울렛', '스타필드', '이마트', '홈플러스', '롯데마트'],
  P13: ['영화', 'CGV', '롯데시네마', '메가박스', '인터파크티켓', '티켓링크', '미술관', '박물관', '공연', '연극'],
};

const normalize = (value: string) =>
  (value || '').toLowerCase().replace(/\s+/g, '_').replace(/[-/]/g, '_');

const amountToNumber = (value: string | number | undefined) => {
  if (typeof value === 'number') return value;
  if (!value) return 0;
  const digits = String(value).replace(/[^\d-]/g, '');
  return Number(digits || 0);
};

const monthRange = (month: string) => {
  const [y, m] = month.split('-').map(Number);
  const first = new Date(y, m - 1, 1);
  const last = new Date(y, m, 0);
  const fmt = (d: Date) =>
    `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
  return { startDate: fmt(first), endDate: fmt(last) };
};

const detectType = (tx: TransactionItemDto): string | null => {
  const categoryKey = normalize(tx.categoryName || '');
  if (CATEGORY_TO_TYPE[categoryKey]) return CATEGORY_TO_TYPE[categoryKey];

  const merged = `${tx.merchantName || ''} ${tx.categoryName || ''}`.toLowerCase();
  for (const [type, keywords] of Object.entries(STORE_KEYWORDS)) {
    if (keywords.some((kw) => merged.includes(kw.toLowerCase()))) return type;
  }
  return null;
};

export const CardRecommendationDetailPage = () => {
  const navigate = useNavigate();
  const { recommendCardId } = useParams<{ recommendCardId: string }>();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [selectedCard, setSelectedCard] = useState<CardResult | null>(null);
  const [benefitLines, setBenefitLines] = useState<BenefitLine[]>([]);

  const month = useMemo(() => {
    const q = searchParams.get('month');
    if (q && /^\d{4}-\d{2}$/.test(q)) return q;
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }, [searchParams]);

  useEffect(() => {
    const run = async () => {
      if (!recommendCardId) return;
      try {
        setLoading(true);
        const rec = (await getCardRecommendation(month)) as CardRecommendationResponse;
        const card =
          rec?.all_cards?.find((x) => String(x.card_id) === String(recommendCardId)) || null;
        setSelectedCard(card);
        if (!card) return;

        const { startDate, endDate } = monthRange(month);
        const cardsRes = await getMyCards();
        const cards = (cardsRes as any)?.cards || [];

        const txResponses = await Promise.all(
          cards.map((c: { id: number }) =>
            getCardTransactions(String(c.id), startDate, endDate).catch(() => null)
          )
        );

        const allTx: TransactionItemDto[] = txResponses
          .flatMap((res: any) => (res?.transaction ? res.transaction : []))
          .filter(Boolean);

        const spendByType = new Map<string, number>();
        const merchantByType = new Map<string, Map<string, number>>();

        allTx.forEach((tx) => {
          const type = detectType(tx);
          if (!type) return;
          const amount = amountToNumber(tx.transactionAmount);
          spendByType.set(type, (spendByType.get(type) || 0) + amount);

          if (!merchantByType.has(type)) merchantByType.set(type, new Map<string, number>());
          const mMap = merchantByType.get(type)!;
          const name = tx.merchantName || '기타';
          mMap.set(name, (mMap.get(name) || 0) + amount);
        });

        const lines: BenefitLine[] = (card.structured_benefits || []).map((b) => {
          const spent = spendByType.get(b.target_type) || 0;
          const merchants = Array.from(merchantByType.get(b.target_type)?.entries() || [])
            .sort((a, z) => z[1] - a[1])
            .slice(0, 5)
            .map(([name, amount]) => ({ name, amount }));
          return {
            targetType: b.target_type,
            rate: b.rate || 0,
            typeLabel: TYPE_LABELS[b.target_type] || b.target_type,
            spentAmount: spent,
            estimatedDiscount: Math.floor(spent * (b.rate || 0)),
            merchants,
          };
        });
        setBenefitLines(lines);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [recommendCardId, month]);

  const totalEstimatedDiscount = useMemo(
    () => benefitLines.reduce((sum, row) => sum + row.estimatedDiscount, 0),
    [benefitLines]
  );

  if (loading) {
    return (
      <div className="w-full max-w-[900px] mx-auto py-20 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-gray-200 border-t-indigo-600 rounded-full animate-spin" />
      </div>
    );
  }

  if (!selectedCard) {
    return (
      <div className="w-full max-w-[900px] mx-auto py-20 text-center">
        <p className="text-gray-700 font-bold">추천 카드 정보를 찾을 수 없습니다.</p>
        <button
          onClick={() => navigate('/finance/cards/recommendation')}
          className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 text-white"
        >
          추천 목록으로
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-[980px] mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="p-2 rounded-lg hover:bg-gray-100">
          ←
        </button>
        <h1 className="text-2xl font-black text-gray-900">추천 카드 상세 근거</h1>
      </div>

      <div className="bg-white border border-gray-100 rounded-2xl p-6 mb-5">
        <p className="text-indigo-600 font-bold text-sm">{selectedCard.name}</p>
        <h2 className="text-2xl font-extrabold mt-1">{selectedCard.main_text}</h2>
        <p className="text-gray-500 mt-2 text-sm">기준월: {month}</p>
        <div className="mt-4 text-right">
          <p className="text-gray-500 text-sm">예상 월 할인액</p>
          <p className="text-3xl font-black text-indigo-600">{totalEstimatedDiscount.toLocaleString()}원</p>
        </div>
      </div>

      <div className="space-y-4">
        {benefitLines.map((line) => (
          <div key={`${line.targetType}-${line.rate}`} className="bg-white border border-gray-100 rounded-2xl p-5">
            <div className="flex items-center justify-between">
              <h3 className="font-extrabold text-lg">{line.typeLabel}</h3>
              <p className="font-bold text-indigo-600">{Math.round(line.rate * 100)}%</p>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              사용금액 {line.spentAmount.toLocaleString()}원 × 할인율 {Math.round(line.rate * 100)}%
            </div>
            <div className="mt-1 text-xl font-black text-gray-900">
              예상 할인 {line.estimatedDiscount.toLocaleString()}원
            </div>
            <div className="mt-3">
              <p className="text-sm font-bold text-gray-700 mb-2">실제 사용 가맹점(상위)</p>
              {line.merchants.length === 0 ? (
                <p className="text-sm text-gray-400">해당 타입 사용 내역 없음</p>
              ) : (
                <ul className="space-y-1">
                  {line.merchants.map((m) => (
                    <li key={m.name} className="text-sm text-gray-700 flex justify-between">
                      <span>{m.name}</span>
                      <span className="font-semibold">{m.amount.toLocaleString()}원</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
