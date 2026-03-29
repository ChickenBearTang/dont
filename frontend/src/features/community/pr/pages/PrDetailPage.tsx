import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card } from '@/shared/components';
import { closePr, getPrDetail, submitPrVote } from '@/features/community/pr';
import type { PrDetailResponseData } from '@/features/community/pr';
import { getPrXaiAvailability, getPrXaiEvaluation } from '@/features/community/pr/api/prXaiApi';
import type {
  PrXaiAvailabilityResponseData,
  PrXaiEvaluationResponseData,
} from '@/features/community/pr/xaiTypes';
import { useUIStore } from '@/shared/store/useUIStore';
import { formatRelativeTime } from '@/shared/utils/date';
import { UserAvatar } from '@/features/community/components/UserAvatar';

const formatCurrency = (value: number): string =>
  new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(value);

const formatDateTime = (value: string | null): string => {
  if (!value) return '-';
  return new Date(value).toLocaleString('ko-KR');
};

const formatAbsoluteDate = (value: string): string =>
  new Date(value).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

const normalizePrStatus = (status: string): string => status.trim().toUpperCase();

const getStatusLabelWithEmoji = (status: string): string => {
  const normalized = normalizePrStatus(status);
  if (normalized === 'OPEN') return '📂 OPEN';
  if (normalized === 'MERGED') return '✔️ MERGED';
  if (normalized === 'CLOSED') return '🚫 CLOSED';
  return normalized;
};

const getStatusBadgeClass = (status: string): string => {
  const normalizedStatus = normalizePrStatus(status);

  if (normalizedStatus === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (normalizedStatus === 'MERGED') return 'bg-green-50 text-green-700 border-green-200';
  if (normalizedStatus === 'CLOSED') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const getTimelineDotClass = (type: 'base' | 'review' | 'status', decision?: string): string => {
  if (type === 'review') {
    return decision === 'APPROVE' ? 'bg-success' : 'bg-danger';
  }
  if (type === 'status') return 'bg-accent';
  return 'bg-primary-blue';
};

interface TimelineEvent {
  id: string;
  type: 'base' | 'review' | 'status';
  title: string;
  subTitle: string;
  content: string;
  timeLabel: string;
  actorLabel?: string;
  decision?: string;
}

interface EventPayload {
  title?: string;
  itemName?: string;
  priceAmount?: number;
  decision?: string;
  voteValue?: string;
  opinionText?: string;
  before?: string;
  after?: string;
  closeReason?: string;
}

interface ContentSection {
  title: string;
  body: string;
}

interface XaiSummaryParts {
  verdict: string;
  keyReason: string;
  improvementPoint: string;
}

const decisionLabelMap: Record<string, string> = {
  BUY_NOW: '지금 구매 권장',
  WAIT: '관망 권장',
  REVIEW: '추가 검토 필요',
  NOT_RECOMMENDED: '비구매 권장',
};

const getDecisionBadgeClass = (decision: string): string => {
  const normalized = decision.trim().toUpperCase();
  if (normalized === 'BUY_NOW') return 'bg-success/10 text-success ring-1 ring-success/30';
  if (normalized === 'WAIT') return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200';
  if (normalized === 'NOT_RECOMMENDED') return 'bg-danger/10 text-danger ring-1 ring-danger/30';
  return 'bg-slate-100 text-slate-700 ring-1 ring-slate-200';
};

const formatPercent = (value: number): string => `${Math.round(value * 100)}%`;

const formatImpactPercent = (value: number): string => {
  const absoluteValue = Math.abs(value);
  if (absoluteValue <= 1) return `${Math.round(absoluteValue * 100)}%`;
  if (absoluteValue <= 100) return `${Math.round(absoluteValue)}%`;
  return `${Math.round(Math.min(absoluteValue / 100, 100))}%`;
};

const parseMetricNumericValue = (rawValue: string): number | null => {
  const sanitized = rawValue.replace(/[^\d.-]/g, '');
  if (!sanitized) return null;
  const parsed = Number(sanitized);
  if (!Number.isFinite(parsed)) return null;
  return parsed;
};

const toComparisonBarPercent = (value: number, maxValue: number): number => {
  if (value <= 0 || maxValue <= 0) return 0;
  const rawPercent = (value / maxValue) * 100;
  return Math.min(Math.max(rawPercent, 8), 100);
};

const formatWon = (value: number): string => `${Math.round(value).toLocaleString('ko-KR')}원`;

const normalizeMetricCode = (code: string): string =>
  code.trim().toLowerCase().replace(/[\s-]+/g, '_');

const normalizeMetricLabelToken = (label: string): string => label.replace(/\s+/g, '').trim();

const isCurrentPriceMetric = (code: string, label: string): boolean => {
  const normalizedCode = normalizeMetricCode(code);
  const normalizedLabel = normalizeMetricLabelToken(label);
  return (
    normalizedCode === 'current_price' ||
    normalizedCode === 'price_current' ||
    normalizedLabel.includes('현재판단가격') ||
    normalizedLabel.includes('현재가격')
  );
};

const isAvgPriceMetric = (code: string, label: string): boolean => {
  const normalizedCode = normalizeMetricCode(code);
  const normalizedLabel = normalizeMetricLabelToken(label);
  return (
    normalizedCode === 'avg_price_30d' ||
    normalizedCode === 'average_price_30d' ||
    normalizedCode === 'price_avg_30d' ||
    normalizedLabel.includes('30일평균가') ||
    normalizedLabel.includes('평균가')
  );
};

const toDisplayMetricLabel = (label: string): string => {
  const normalizedLabel = normalizeMetricLabelToken(label);
  if (normalizedLabel === '사용가능고정지출') return '이번 달 고정지출';
  if (normalizedLabel === '사용가능고정수입') return '이번 달 고정 수입';
  return label;
};

const xaiSectionStatusLabelMap: Record<string, string> = {
  critical: '위험',
  tight: '주의',
  healthy: '양호',
  degraded: '데이터 부족',
  favorable: '유리',
  expensive: '고가',
  neutral: '보통',
};

const xaiWarningLabelMap: Record<string, string> = {
  CRAWL_FETCH_FAILED: '상품 페이지 크롤링에 실패했습니다.',
  PRICE_ESTIMATED_FROM_REQUEST: '요청 가격 기준으로 대체 계산했습니다.',
  SHAP_UNAVAILABLE: 'SHAP 설명 엔진을 사용할 수 없습니다.',
  DICE_UNAVAILABLE: 'DICE 반사실 설명 엔진을 사용할 수 없습니다.',
  NO_PRICE_HISTORY: '가격 이력 데이터가 부족합니다.',
  PRICE_HISTORY_READ_FAILED: '가격 이력 조회에 실패했습니다.',
  MISSING_PURCHASE_URL: '구매 URL이 없어 크롤링을 생략했습니다.',
  FINANCE_PROFILE_EMPTY_FALLBACK: '재무 데이터가 부족해 가격 중심으로 판단했습니다.',
};

const getXaiSectionStatusLabel = (status: string): string =>
  xaiSectionStatusLabelMap[status.trim().toLowerCase()] ?? status;

const getXaiWarningLabel = (warning: string): string => xaiWarningLabelMap[warning] ?? warning;

const cleanSummarySegment = (value: string): string =>
  value.replace(/^[\s.·\-:]+/, '').replace(/\s+/g, ' ').trim();

const parseXaiSummary = (summary: string): XaiSummaryParts => {
  const raw = summary ?? '';
  const keyMarker = '핵심 근거:';
  const improveMarker = '개선 포인트:';
  const keyIndex = raw.indexOf(keyMarker);
  const improveIndex = raw.indexOf(improveMarker);

  const normalizeVerdict = (value: string): string =>
    cleanSummarySegment(value).replace(/[.。]+$/, '').trim();

  if (keyIndex < 0 && improveIndex < 0) {
    return {
      verdict: normalizeVerdict(raw) || '-',
      keyReason: '-',
      improvementPoint: '-',
    };
  }

  const verdictEndCandidates = [keyIndex, improveIndex].filter((index) => index >= 0);
  const verdictEnd =
    verdictEndCandidates.length > 0 ? Math.min(...verdictEndCandidates) : raw.length;

  const keyReasonStart = keyIndex >= 0 ? keyIndex + keyMarker.length : -1;
  const keyReasonEnd = improveIndex >= 0 ? improveIndex : raw.length;
  const keyReason =
    keyReasonStart >= 0 ? cleanSummarySegment(raw.slice(keyReasonStart, keyReasonEnd)) : '-';

  const improvementStart = improveIndex >= 0 ? improveIndex + improveMarker.length : -1;
  const improvementPoint =
    improvementStart >= 0 ? cleanSummarySegment(raw.slice(improvementStart)) : '-';

  return {
    verdict: normalizeVerdict(raw.slice(0, verdictEnd)) || '-',
    keyReason: keyReason || '-',
    improvementPoint: improvementPoint || '-',
  };
};

const xaiEvidenceFieldLabelMap: Record<string, string> = {
  current_price: '현재 판단 가격',
  projected_balance_after_purchase: '구매 후 예상 잔액',
  days_until_card_due: '카드 결제일까지',
  avg_price_30d: '30일 평균가',
  emergency_fund_balance: '비상자금',
  current_balance: '현재 잔액',
};

const xaiEvidenceSourceLabelMap: Record<string, string> = {
  'spring.pr_post': 'PR 요청값',
  'spring.finance_profile': '재무 프로필',
  'fastapi.xai': 'AI 계산값',
};

const getXaiEvidenceFieldLabel = (field: string): string => {
  if (field === 'projected_balance_after_purchase') {
    return '구매 후 세이브박스 잔액';
  }
  return xaiEvidenceFieldLabelMap[field] ?? field;
};

const getXaiEvidenceSourceLabel = (source: string): string =>
  xaiEvidenceSourceLabelMap[source] ?? source;

const formatXaiEvidenceValue = (field: string, rawValue: string): string => {
  const normalized = rawValue.trim();
  if (normalized.length === 0) return rawValue;
  const numeric = Number(normalized.replaceAll(',', ''));
  if (!Number.isFinite(numeric)) return rawValue;

  if (field === 'days_until_card_due') return `${Math.round(numeric)}일`;
  if (
    field === 'current_price' ||
    field === 'projected_balance_after_purchase' ||
    field === 'avg_price_30d' ||
    field === 'emergency_fund_balance' ||
    field === 'current_balance'
  ) {
    return `${Math.round(numeric).toLocaleString('ko-KR')}원`;
  }
  return rawValue;
};

const parseEventPayload = (payload: Record<string, unknown> | null): EventPayload => {
  if (!payload) return {};
  return payload as EventPayload;
};

const parseContentSections = (content: string): ContentSection[] => {
  const knownHeadings = ['왜 필요한가?', '예산은 적절한가?', '대체재는 없는가?'];
  const lines = content.split('\n');
  const sections: ContentSection[] = [];
  let currentTitle: string | null = null;
  let buffer: string[] = [];

  const flush = () => {
    if (!currentTitle) {
      return;
    }

    sections.push({
      title: currentTitle,
      body: buffer.join('\n').trim(),
    });
    buffer = [];
  };

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (knownHeadings.includes(trimmed)) {
      flush();
      currentTitle = trimmed;
      return;
    }
    buffer.push(line);
  });

  flush();

  if (sections.length > 0) {
    return sections;
  }

  return [
    {
      title: '구매 요청 내용',
      body: content.trim(),
    },
  ];
};

const buildTimelineEvents = (detail: PrDetailResponseData): TimelineEvent[] => {
  if (detail.events && detail.events.length > 0) {
    return detail.events.map((event) => {
      const payload = parseEventPayload(event.payload);

      if (event.eventType === 'REVIEW_SUBMITTED') {
        const isApprove = payload.decision === 'APPROVE';
        const actorName = event.actorNickname ?? `사용자 #${event.actorUserId ?? '-'}`;
        const reviewSummary = isApprove
          ? `${actorName}님이 승인 의견을 남겼습니다.`
          : `${actorName}님이 변경 요청 의견을 남겼습니다.`;
        return {
          id: `event-${event.eventId}`,
          type: 'review',
          title: isApprove ? 'Approve 리뷰 등록' : 'Reject 리뷰 등록',
          subTitle: payload.decision ? `결정: ${payload.decision}` : '리뷰가 등록되었습니다.',
          content:
            payload.opinionText && payload.opinionText.trim().length > 0
              ? payload.opinionText
              : reviewSummary,
          timeLabel: formatRelativeTime(event.createdAt),
          actorLabel: event.actorNickname ?? undefined,
          decision: payload.decision,
        };
      }

      if (event.eventType === 'STATUS_CHANGED') {
        return {
          id: `event-${event.eventId}`,
          type: 'status',
          title: '상태 변경',
          subTitle:
            payload.before && payload.after
              ? `${payload.before} -> ${payload.after}`
              : `현재 상태: ${detail.status}`,
          content: payload.closeReason
            ? `종료 사유: ${payload.closeReason}`
            : '요청 상태가 변경되었습니다.',
          timeLabel: formatRelativeTime(event.createdAt),
          actorLabel: event.actorNickname ?? undefined,
        };
      }

      return {
        id: `event-${event.eventId}`,
        type: 'base',
        title: '구매 요청 생성',
        subTitle: `카테고리: ${detail.category ?? '미지정'}`,
        content:
          payload.title && payload.itemName ? `${payload.title} / ${payload.itemName}` : detail.title,
        timeLabel: formatRelativeTime(event.createdAt),
        actorLabel: event.actorNickname ?? undefined,
      };
    });
  }

  return [
    {
      id: 'base-fallback',
      type: 'base',
      title: '구매 요청 생성',
      subTitle: `카테고리: ${detail.category ?? '미지정'}`,
      content: detail.title,
      timeLabel: '요청 등록',
    },
    ...(detail.totalVoteCount > 0
      ? [
          {
            id: 'review-fallback',
            type: 'review' as const,
            title: '리뷰 투표 집계',
            subTitle: `Approve ${detail.agreeCount} / Reject ${detail.disagreeCount}`,
            content: '리뷰어 투표가 반영되었습니다.',
            timeLabel: `총 ${detail.totalVoteCount}명 참여`,
          },
        ]
      : []),
    ...(detail.status !== 'OPEN'
      ? [
          {
            id: 'status-fallback',
            type: 'status' as const,
            title: `요청 상태 변경 (${detail.status})`,
            subTitle: `현재 상태: ${detail.status}`,
            content: '해당 구매 요청은 종료되어 더 이상 리뷰를 받을 수 없습니다.',
            timeLabel: `종료 시각: ${formatDateTime(detail.closedAt)}`,
          },
        ]
      : []),
  ];
};

export const PrDetailPage = () => {
  const navigate = useNavigate();
  const { postId } = useParams<{ postId: string }>();
  const { addToast } = useUIStore();

  const parsedPostId = useMemo(() => Number(postId), [postId]);

  const [detail, setDetail] = useState<PrDetailResponseData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [voteOpinion, setVoteOpinion] = useState('');
  const [isSubmittingVote, setIsSubmittingVote] = useState(false);
  const [isClosingPr, setIsClosingPr] = useState(false);
  const [xaiEvaluation, setXaiEvaluation] = useState<PrXaiEvaluationResponseData | null>(null);
  const [xaiAvailability, setXaiAvailability] = useState<PrXaiAvailabilityResponseData | null>(null);
  const [isXaiAvailabilityLoading, setIsXaiAvailabilityLoading] = useState(false);
  const [isXaiLoading, setIsXaiLoading] = useState(false);
  const [xaiError, setXaiError] = useState<string | null>(null);
  const [hasRequestedXai, setHasRequestedXai] = useState(false);

  const loadDetail = useCallback(async () => {
    if (!parsedPostId || Number.isNaN(parsedPostId)) {
      setErrorMessage('유효하지 않은 PR 번호입니다.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await getPrDetail(parsedPostId);
      setDetail(response.data);
    } catch {
      setDetail(null);
      setErrorMessage('PR 상세 정보를 불러오지 못했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [parsedPostId]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  useEffect(() => {
    setXaiEvaluation(null);
    setXaiAvailability(null);
    setIsXaiAvailabilityLoading(false);
    setXaiError(null);
    setIsXaiLoading(false);
    setHasRequestedXai(false);
  }, [parsedPostId]);

  useEffect(() => {
    if (!detail) return;
    let isMounted = true;

    const loadAvailability = async () => {
      setIsXaiAvailabilityLoading(true);
      try {
        const response = await getPrXaiAvailability(detail.postId);
        if (!isMounted) return;
        setXaiAvailability(response.data);
      } catch {
        if (!isMounted) return;
        setXaiAvailability({
          enabled: false,
          reason: 'XAI 활성화 상태를 확인하지 못했습니다.',
        });
      } finally {
        if (isMounted) {
          setIsXaiAvailabilityLoading(false);
        }
      }
    };

    void loadAvailability();
    return () => {
      isMounted = false;
    };
  }, [detail]);

  const handleFetchXaiEvaluation = useCallback(async () => {
    if (!detail || isXaiLoading || !xaiAvailability?.enabled) return;

    setHasRequestedXai(true);
    setXaiEvaluation(null);
    setIsXaiLoading(true);
    setXaiError(null);

    try {
      const response = await getPrXaiEvaluation(detail.postId);
      setXaiEvaluation(response.data);
    } catch {
      setXaiEvaluation(null);
      setXaiError('XAI 구매 판단 결과를 불러오지 못했습니다.');
    } finally {
      setIsXaiLoading(false);
    }
  }, [detail, isXaiLoading, xaiAvailability?.enabled]);

  const handleVote = async (voteValue: 'AGREE' | 'DISAGREE') => {
    if (!detail || detail.status !== 'OPEN' || isSubmittingVote) return;

    setIsSubmittingVote(true);
    try {
      await submitPrVote(detail.postId, {
        voteValue,
        opinionText: voteOpinion.trim() || undefined,
      });
      addToast('투표가 등록되었습니다.', 'success');
      setVoteOpinion('');
      await loadDetail();
    } catch {
      addToast('투표 등록에 실패했습니다.', 'error');
    } finally {
      setIsSubmittingVote(false);
    }
  };

  const handleClosePr = async (resultStatus: 'MERGED' | 'CLOSED') => {
    if (!detail || detail.status !== 'OPEN' || isClosingPr) return;

    setIsClosingPr(true);
    try {
      await closePr(detail.postId, { resultStatus });
      addToast(`PR이 ${resultStatus} 상태로 종료되었습니다.`, 'success');
      await loadDetail();
    } catch {
      addToast('PR 종료에 실패했습니다. 작성자만 종료할 수 있습니다.', 'error');
    } finally {
      setIsClosingPr(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-64 bg-gray-100 rounded-xl animate-pulse" />
        <Card className="h-72 animate-pulse bg-gray-50 border-gray-100">
          <div className="h-full" />
        </Card>
      </div>
    );
  }

  if (errorMessage || !detail) {
    return (
      <Card className="flex flex-col items-center gap-4 py-12 text-center">
        <h2 className="text-xl font-black text-gray-800">PR 상세 오류</h2>
        <p className="text-gray-500 font-medium">
          {errorMessage ?? '예상치 못한 오류가 발생했습니다.'}
        </p>
        <Button
          type="button"
          className="!w-auto px-6 py-2.5 text-sm"
          onClick={() => void loadDetail()}
        >
          다시 시도
        </Button>
      </Card>
    );
  }

  const isOpen = detail.status === 'OPEN';
  const canVote = detail.permissions?.canVote ?? isOpen;
  const canClose = detail.permissions?.canClose ?? isOpen;
  const voteDisabledReason = detail.permissions?.voteDisabledReason ?? '투표할 수 없습니다.';
  const agreeRatio =
    detail.totalVoteCount > 0 ? (detail.agreeCount / detail.totalVoteCount) * 100 : 0;
  const timelineEvents = buildTimelineEvents(detail);
  const contentSections = parseContentSections(detail.content);
  const primaryAttachment = detail.attachments[0] ?? null;
  const latestEventTime =
    detail.events && detail.events.length > 0
      ? detail.events[detail.events.length - 1].createdAt
      : detail.closedAt ?? detail.updatedAt;
  const xaiSummaryParts = xaiEvaluation ? parseXaiSummary(xaiEvaluation.summary) : null;
  const priceMetrics = xaiEvaluation
    ? xaiEvaluation.priceEvaluation.keyMetrics.filter(
        (metric) => metric.code !== 'requested_price_amount',
      )
    : [];
  const priceComparison = (() => {
    const currentPriceMetric = priceMetrics.find((metric) =>
      isCurrentPriceMetric(metric.code, metric.label),
    );
    const averagePriceMetric = priceMetrics.find((metric) =>
      isAvgPriceMetric(metric.code, metric.label),
    );
    if (!currentPriceMetric || !averagePriceMetric) return null;

    const currentPrice = parseMetricNumericValue(currentPriceMetric.value);
    const averagePrice = parseMetricNumericValue(averagePriceMetric.value);
    if (currentPrice === null || averagePrice === null) return null;

    const maxPrice = Math.max(currentPrice, averagePrice, 1);
    const gap = currentPrice - averagePrice;
    const ratio = averagePrice > 0 ? currentPrice / averagePrice : null;

    if (gap > 0) {
      return {
        currentPrice,
        averagePrice,
        currentPriceLabel: currentPriceMetric.value,
        averagePriceLabel: averagePriceMetric.value,
        currentBarPercent: toComparisonBarPercent(currentPrice, maxPrice),
        averageBarPercent: toComparisonBarPercent(averagePrice, maxPrice),
        headlineText: '현재 판단 가격 > 30일 평균가',
        summaryText: `현재 판단 가격이 평균가보다 ${formatWon(Math.abs(gap))} 높습니다.`,
        detailText: ratio ? `평균가의 ${ratio.toFixed(2)}배` : null,
        summaryClassName: 'text-danger',
      };
    }

    if (gap < 0) {
      return {
        currentPrice,
        averagePrice,
        currentPriceLabel: currentPriceMetric.value,
        averagePriceLabel: averagePriceMetric.value,
        currentBarPercent: toComparisonBarPercent(currentPrice, maxPrice),
        averageBarPercent: toComparisonBarPercent(averagePrice, maxPrice),
        headlineText: '현재 판단 가격 < 30일 평균가',
        summaryText: `현재 판단 가격이 평균가보다 ${formatWon(Math.abs(gap))} 낮습니다.`,
        detailText: ratio ? `평균가의 ${ratio.toFixed(2)}배` : null,
        summaryClassName: 'text-success',
      };
    }

    return {
      currentPrice,
      averagePrice,
      currentPriceLabel: currentPriceMetric.value,
      averagePriceLabel: averagePriceMetric.value,
      currentBarPercent: toComparisonBarPercent(currentPrice, maxPrice),
      averageBarPercent: toComparisonBarPercent(averagePrice, maxPrice),
      headlineText: '현재 판단 가격 = 30일 평균가',
      summaryText: '현재 판단 가격과 30일 평균가가 같습니다.',
      detailText: null,
      summaryClassName: 'text-text-muted',
    };
  })();
  const priceMetricList = priceComparison
    ? priceMetrics.filter(
        (metric) =>
          !isCurrentPriceMetric(metric.code, metric.label) &&
          !isAvgPriceMetric(metric.code, metric.label),
      )
    : priceMetrics;
  const financialMetricValueByCode = xaiEvaluation
    ? new Map(
        xaiEvaluation.financialEvaluation.keyMetrics.map((metric) => [metric.code, metric.value]),
      )
    : new Map<string, string>();
  const saveboxBalanceLabel = financialMetricValueByCode.get('savebox_balance') ?? '-';
  const fixedExpenseLabel =
    financialMetricValueByCode.get('available_fixed_expense') ??
    financialMetricValueByCode.get('monthly_fixed_expense') ??
    '-';
  const fixedIncomeLabel =
    financialMetricValueByCode.get('available_fixed_income') ??
    financialMetricValueByCode.get('monthly_fixed_income') ??
    '-';
  const cardSpendLabel =
    financialMetricValueByCode.get('expected_card_payment_amount') ??
    financialMetricValueByCode.get('monthly_card_spend') ??
    '-';
  const dueDaysLabel = financialMetricValueByCode.get('days_until_card_due') ?? '-';
  const dueDaysValue = parseMetricNumericValue(dueDaysLabel);
  const dueDayBadge = dueDaysValue === null ? '-' : `D-${Math.max(Math.round(dueDaysValue), 0)}`;

  const saveboxBalanceValue = parseMetricNumericValue(saveboxBalanceLabel) ?? 0;
  const fixedExpenseValue = parseMetricNumericValue(fixedExpenseLabel) ?? 0;
  const fixedIncomeValue = parseMetricNumericValue(fixedIncomeLabel) ?? 0;
  const cardSpendValue = parseMetricNumericValue(cardSpendLabel) ?? 0;
  const financeScaleMax = Math.max(
    saveboxBalanceValue,
    fixedExpenseValue,
    fixedIncomeValue,
    cardSpendValue,
    1,
  );
  const toFinanceBarPercent = (value: number): number =>
    value <= 0 ? 0 : toComparisonBarPercent(value, financeScaleMax);
  const saveboxBarPercent = toFinanceBarPercent(saveboxBalanceValue);
  const fixedExpenseBarPercent = toFinanceBarPercent(fixedExpenseValue);
  const fixedIncomeBarPercent = toFinanceBarPercent(fixedIncomeValue);
  const cardSpendBarPercent = toFinanceBarPercent(cardSpendValue);
  const monthlyCashflowGap = fixedIncomeValue - fixedExpenseValue;
  const monthlyCashflowLabel =
    monthlyCashflowGap >= 0
      ? `+${formatWon(monthlyCashflowGap)}`
      : `-${formatWon(Math.abs(monthlyCashflowGap))}`;
  const monthlyCashflowToneClass = monthlyCashflowGap >= 0 ? 'text-success' : 'text-danger';

  const majorTopFactors = xaiEvaluation ? xaiEvaluation.topFactors.slice(0, 3) : [];
  const priceRatioBadge = priceComparison?.detailText ?? '비교 데이터 부족';
  const isAnalysisVerified = xaiEvaluation
    ? xaiEvaluation.confidence.dataCompleteness >= 0.8 &&
      xaiEvaluation.confidence.explanationFidelity >= 0.8
    : false;
  const analysisStatusLabel = isAnalysisVerified ? '검증 완료' : '추가 확인';
  const analysisStatusClass = isAnalysisVerified
    ? 'bg-green-100 text-green-700'
    : 'bg-amber-100 text-amber-700';

  return (
    <div className="grid grid-cols-1 items-start gap-8 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <span
                className={`rounded-full border px-4 py-1 text-xs font-bold uppercase tracking-wider ${getStatusBadgeClass(detail.status)} shadow-sm`}
              >
                {getStatusLabelWithEmoji(detail.status)}
              </span>
              <span className="text-xs font-bold text-text-subtle tracking-tight bg-surface-soft px-2.5 py-1 rounded-lg">PR #{detail.postId}</span>
            </div>
            <h1 className="text-3xl font-black leading-tight text-eel tracking-tight">{detail.title}</h1>
            <div className="flex items-center gap-3 text-sm font-semibold text-text-muted">
              <UserAvatar
                profileImageUrl={detail.authorProfileImageUrl}
                nickname={detail.authorNickname}
                className="h-9 w-9 border-2 border-white shadow-sm"
              />
              <div>
                <span className="text-eel">{detail.authorNickname}</span>
                <span className="mx-2 text-text-subtle opacity-40">|</span>
                <span className="text-text-subtle font-medium">작성 {formatAbsoluteDate(detail.createdAt)}</span>
                {detail.updatedAt !== detail.createdAt && (
                  <>
                    <span className="mx-2 text-text-subtle opacity-40">|</span>
                    <span className="text-text-subtle font-medium">수정 {formatRelativeTime(detail.updatedAt)}</span>
                  </>
                )}
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            fullWidth={false}
            className="!rounded-2xl !px-6 !py-3 !text-sm"
            onClick={() => navigate('/community/write?category=PR')}
          >
            글쓰기
          </Button>
        </div>

        <Card className="!p-0 overflow-hidden border-2 border-accent-soft/30 shadow-xl hover:shadow-2xl transition-all h-full flex flex-col">
          <div className="flex items-center justify-between gap-4 border-b border-light-gray bg-surface-muted/50 px-8 py-6">
            <div className="min-w-0">
              <p className="text-2xl font-black leading-tight text-eel truncate">{detail.itemName}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-accent animate-pulse" />
                <p className="text-xs font-bold text-text-muted tracking-tight">
                  최근 업데이트 {latestEventTime ? formatRelativeTime(latestEventTime) : '-'}
                </p>
              </div>
            </div>
            {detail.deadlineAt ? (
              <div className="shrink-0 flex flex-col items-end gap-1">
                <span className="text-[10px] uppercase font-black text-text-subtle mb-1">마감 기한</span>
                <span className="rounded-xl border border-danger-soft bg-danger-soft/30 px-3.5 py-1.5 text-xs font-bold text-danger">
                  {formatDateTime(detail.deadlineAt)}
                </span>
              </div>
            ) : null}
          </div>

          <div className="grid grid-cols-1 gap-4 border-b border-light-gray bg-gradient-to-br from-surface-muted via-blue-50/20 to-surface-muted px-8 py-6 md:grid-cols-3">
            <div className="rounded-2xl bg-white/80 p-5 shadow-sm ring-1 ring-light-gray">
              <p className="text-[11px] font-black text-text-subtle uppercase tracking-widest mb-1.5">요청 금액</p>
              <p className="text-2xl font-black text-eel tracking-tighter">
                {formatCurrency(detail.priceAmount)}
              </p>
            </div>
            <div className="rounded-2xl bg-success/5 p-5 shadow-sm border-2 border-success/20 group transition-all hover:bg-success/10 hover:border-success/40">
              <p className="text-[11px] font-black text-success uppercase tracking-widest mb-1.5 group-hover:scale-105 origin-left transition-transform">Approve</p>
              <div className="flex items-baseline gap-1">
                <p className="text-2xl font-black text-success tracking-tighter">
                  {detail.agreeCount}
                </p>
                <span className="text-[13px] font-bold text-success/60">표 참여</span>
              </div>
            </div>
            <div className="rounded-2xl bg-danger/5 p-5 shadow-sm border-2 border-danger/20 group transition-all hover:bg-danger/10 hover:border-danger/40">
              <p className="text-[11px] font-black text-danger uppercase tracking-widest mb-1.5 group-hover:scale-105 origin-left transition-transform">Reject</p>
              <div className="flex items-baseline gap-1">
                <p className="text-2xl font-black text-danger tracking-tighter">
                  {detail.disagreeCount}
                </p>
                <span className="text-[13px] font-bold text-danger/60">표 참여</span>
              </div>
            </div>
          </div>

          <div className="space-y-6 px-8 py-8 flex-1">
            {contentSections.map((section, idx) => (
              <div key={section.title} className={`space-y-3 ${idx !== contentSections.length - 1 ? 'pb-6 border-b border-dashed border-light-gray' : ''}`}>
                <h2 className="text-lg font-black text-eel flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-blue" />
                  {section.title}
                </h2>
                <div className="whitespace-pre-wrap text-[16px] leading-[1.7] text-gray-700 font-medium pl-3.5">
                  {section.body || '내용이 없습니다.'}
                </div>
              </div>
            ))}
            <div className="pt-4 flex items-center gap-2">
               <span className="text-xs font-black text-text-subtle uppercase tracking-tight">Category</span>
               <span className="text-sm font-bold text-eel bg-surface-soft px-3 py-1 rounded-full">{detail.category ?? '-'}</span>
            </div>
          </div>
        </Card>

        <div className="relative space-y-5 pl-12 pt-4">
          <div className="absolute bottom-6 left-5 top-6 w-[2px] bg-gradient-to-b from-primary-blue/30 via-light-gray to-accent/30" />
          {timelineEvents.map((event) => (
            <div key={event.id} className="relative group">
              <span
                className={`absolute -left-[35px] top-6 h-5 w-5 rounded-full border-[3px] border-white shadow-lg transition-transform group-hover:scale-125 z-10 ${getTimelineDotClass(event.type, event.decision)}`}
              />
              <Card className="!p-0 overflow-hidden border-light-gray shadow-sm group-hover:shadow-md transition-all group-hover:-translate-y-1">
                <div className="flex items-center justify-between gap-3 border-b border-light-gray bg-surface-muted px-6 py-4">
                  <div className="flex items-center gap-2.5">
                    <p className="text-sm font-black text-eel uppercase tracking-tight">
                      {event.title}
                    </p>
                    {event.actorLabel && (
                      <span className="rounded-lg bg-white px-2 py-0.5 text-[10px] font-bold text-text-muted border border-light-gray">
                        {event.actorLabel}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] font-bold text-text-subtle uppercase">
                    {event.timeLabel}
                  </span>
                </div>
                <div className="space-y-2 px-6 py-5">
                  <p className="text-[13px] font-bold text-primary-blue/80 tracking-tight">{event.subTitle}</p>
                  <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-eel/80 font-medium">
                    {event.content}
                  </p>
                </div>
              </Card>
            </div>
          ))}
        </div>

        {detail.reviews && detail.reviews.length > 0 ? (
          <Card className="!p-0 overflow-hidden border-light-gray shadow-lg mt-8">
            <div className="flex items-center justify-between border-b border-light-gray bg-eel/[0.02] px-7 py-5">
              <h3 className="text-xl font-black text-eel tracking-tight">리뷰 코맨트</h3>
              <span className="text-xs font-bold text-text-subtle bg-white px-2.5 py-1 rounded-lg border border-light-gray">{detail.reviews.length}건</span>
            </div>
            <div className="divide-y divide-light-gray">
              {detail.reviews.map((review) => (
                <div key={review.reviewId} className="group px-7 py-6 hover:bg-surface-muted/30 transition-colors">
                  <div className="flex items-center gap-3 mb-3">
                    <UserAvatar
                      profileImageUrl={review.userProfileImageUrl}
                      nickname={review.userNickname}
                      className="h-8 w-8 shadow-sm"
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-black text-eel">{review.userNickname ?? `사용자 #${review.userId}`}</span>
                        <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${review.decision === 'APPROVE' ? 'bg-success/10 text-success ring-1 ring-success/20' : 'bg-danger/10 text-danger ring-1 ring-danger/20'}`}>
                          {review.decision}
                        </span>
                      </div>
                      <p className="text-[11px] font-bold text-text-subtle mt-0.5">{formatRelativeTime(review.createdAt)}</p>
                    </div>
                  </div>
                  <div className="bg-white/50 rounded-2xl p-4 ring-1 ring-light-gray group-hover:ring-accent-soft transition-all">
                    <p className="text-[14px] leading-relaxed text-eel/80 font-medium">
                      {review.content && review.content.trim().length > 0
                        ? review.content
                        : '의견 없이 결정만 등록했습니다.'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {!isOpen && (
          <Card className="border-2 border-line-soft bg-surface-muted/30 py-12 text-center shadow-inner overflow-hidden relative">
            <div className="absolute inset-0 bg-pattern-dots opacity-20" />
            <div className="relative z-10">
              <h3 className="text-3xl font-black leading-tight text-eel tracking-tight">
                현재 종료된 요청구루 🐾
              </h3>
              <p className="mt-3 text-lg font-bold text-text-muted">
                최종 결과: <span className="text-accent uppercase">{getStatusLabelWithEmoji(detail.status)}</span>
              </p>
            </div>
          </Card>
        )}
      </section>

      <aside className="space-y-6 xl:sticky xl:top-24 mt-4 xl:mt-0">
        <Card className="!p-0 overflow-hidden border-light-gray shadow-xl hover:shadow-2xl transition-all h-full">
          <div className="border-b border-light-gray bg-surface-muted/50 px-6 py-5">
            <h3 className="text-xl font-black text-eel tracking-tight">대상 상품</h3>
          </div>
          <div className="p-6 space-y-5">
            <div className="relative group overflow-hidden rounded-[24px] border border-light-gray shadow-inner bg-surface-soft">
              {primaryAttachment && primaryAttachment.contentType.startsWith('image/') ? (
                <img
                  src={primaryAttachment.fileUrl}
                  alt={primaryAttachment.fileName}
                  className="h-56 w-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="flex h-56 w-full items-center justify-center text-text-subtle">
                  <svg className="w-12 h-12 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              )}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/40 to-transparent h-12" />
            </div>

            <div className="space-y-1">
              <p className="text-xl font-black text-eel leading-tight tracking-tight">{detail.itemName}</p>
              <p className="text-xs font-bold text-text-subtle uppercase tracking-widest">{detail.category || '기타'}</p>
            </div>

            <div className="flex items-baseline gap-1">
              <p className="text-4xl font-black text-eel tracking-tighter">
                {detail.priceAmount.toLocaleString()}
              </p>
              <span className="text-xl font-black text-eel/40">원</span>
            </div>

            {detail.purchaseUrl ? (
              <a
                href={detail.purchaseUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-2 w-full rounded-2xl bg-brand-night py-4 text-center text-lg font-black text-white transition-all hover:bg-brand-night/90 hover:-translate-y-1 shadow-lg active:scale-95"
              >
                구매처 바로가기
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
            ) : null}

            {detail.attachments.length > 0 ? (
              <div className="rounded-2xl border border-light-gray bg-surface-muted p-4">
                <p className="text-[11px] font-black text-text-subtle uppercase tracking-widest mb-3">첨부파일 {detail.attachments.length}</p>
                <div className="space-y-2">
                  {detail.attachments.map((attachment) => (
                    <a
                      key={attachment.attachmentId}
                      href={attachment.fileUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between gap-3 rounded-xl bg-white p-3 text-xs font-bold text-eel shadow-sm ring-1 ring-light-gray hover:ring-primary-blue hover:text-primary-blue transition-all"
                    >
                      <span className="truncate flex-1">{attachment.fileName}</span>
                      <span className="shrink-0 text-text-subtle font-medium">
                        {Math.max(1, Math.round(attachment.fileSize / 1024))}KB
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border-light-gray shadow-xl">
          <div className="flex items-center justify-between border-b border-light-gray bg-surface-muted/50 px-6 py-5">
            <h3 className="text-xl font-black text-eel tracking-tight">XAI 구매 판단</h3>
            {xaiEvaluation ? (
              <span
                className={`rounded-full px-3 py-1 text-[11px] font-black uppercase tracking-wider ${getDecisionBadgeClass(xaiEvaluation.decision)}`}
              >
                {decisionLabelMap[xaiEvaluation.decision] ?? xaiEvaluation.decision}
              </span>
            ) : null}
          </div>
          <div className="p-6 space-y-4">
            {isXaiLoading ? (
              <div className="flex items-center gap-2 text-sm font-semibold text-text-muted">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-light-gray border-t-primary-blue" />
                XAI가 재무·가격·근거를 분석하고 있습니다.
              </div>
            ) : xaiError ? (
              <div className="space-y-3">
                <p className="rounded-xl border border-danger/20 bg-danger/5 px-3 py-2 text-sm font-semibold text-danger">
                  {xaiError}
                </p>
                {isXaiAvailabilityLoading ? (
                  <p className="text-xs font-semibold text-text-subtle">
                    XAI 활성화 가능 여부를 확인 중입니다.
                  </p>
                ) : (
                  <p className="text-xs font-semibold text-text-subtle">
                    {xaiAvailability?.reason ?? 'XAI 활성화 상태 정보가 없습니다.'}
                  </p>
                )}
                <Button
                  type="button"
                  className="!w-auto !rounded-xl !px-4 !py-2 !text-xs"
                  onClick={() => void handleFetchXaiEvaluation()}
                >
                  다시 판단하기
                </Button>
              </div>
            ) : xaiEvaluation ? (
              <div className="space-y-4">
                <div className="rounded-2xl border border-light-gray bg-gradient-to-br from-amber-50 via-white to-surface-muted p-4 shadow-sm">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[11px] font-black uppercase tracking-widest text-primary-blue">
                        최종 XAI 판단 결과
                      </p>
                      <p className="mt-2 break-keep text-3xl font-black leading-tight text-eel">
                        {decisionLabelMap[xaiEvaluation.decision] ?? xaiEvaluation.decision}
                      </p>
                    </div>
                    <span
                      className={`inline-flex shrink-0 items-center rounded-full px-3 py-1 text-xs font-black ${analysisStatusClass}`}
                    >
                      {analysisStatusLabel}
                    </span>
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    <div className="rounded-xl border border-light-gray bg-white/90 px-2 py-2 text-center">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-text-subtle">
                        판단 신뢰도
                      </p>
                      <p className="mt-1 text-lg font-black text-eel">
                        {formatPercent(xaiEvaluation.confidence.decisionConfidence)}
                      </p>
                    </div>
                    <div className="rounded-xl border border-light-gray bg-white/90 px-2 py-2 text-center">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-text-subtle">
                        데이터 완성도
                      </p>
                      <p className="mt-1 text-lg font-black text-eel">
                        {formatPercent(xaiEvaluation.confidence.dataCompleteness)}
                      </p>
                    </div>
                    <div className="rounded-xl border border-light-gray bg-white/90 px-2 py-2 text-center">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-text-subtle">
                        설명 충실도
                      </p>
                      <p className="mt-1 text-lg font-black text-eel">
                        {formatPercent(xaiEvaluation.confidence.explanationFidelity)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 space-y-1.5 rounded-xl border border-light-gray bg-white/80 px-3 py-2 text-sm font-semibold leading-relaxed text-eel/85">
                    <p className="font-black text-eel">판단 요약</p>
                    <p>{xaiSummaryParts?.verdict ?? '-'}</p>
                    <p>핵심 근거: {xaiSummaryParts?.keyReason ?? '-'}</p>
                    <p>개선 포인트: {xaiSummaryParts?.improvementPoint ?? '-'}</p>
                  </div>
                </div>

                <div className="space-y-3 rounded-2xl border border-light-gray bg-white p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-black text-eel">가격 평가 및 비교</p>
                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-black text-amber-700">
                      {priceRatioBadge}
                    </span>
                  </div>
                  <p className="text-xs font-bold text-text-muted">
                    상태: {getXaiSectionStatusLabel(xaiEvaluation.priceEvaluation.status)}
                  </p>
                  {priceComparison ? (
                    <div className="rounded-xl border border-light-gray bg-surface-muted/40 p-3">
                      <div className="space-y-2">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs font-semibold text-eel/80">
                            <span>현재 판단 가격</span>
                            <span>{priceComparison.currentPriceLabel}</span>
                          </div>
                          <div className="h-2.5 overflow-hidden rounded-full bg-light-gray">
                            <div
                              className="h-full rounded-full bg-primary-blue transition-all duration-700"
                              style={{ width: `${priceComparison.currentBarPercent}%` }}
                            />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs font-semibold text-eel/80">
                            <span>30일 평균가</span>
                            <span>{priceComparison.averagePriceLabel}</span>
                          </div>
                          <div className="h-2.5 overflow-hidden rounded-full bg-light-gray">
                            <div
                              className="h-full rounded-full bg-slate-300 transition-all duration-700"
                              style={{ width: `${priceComparison.averageBarPercent}%` }}
                            />
                          </div>
                        </div>
                      </div>
                      <p className={`mt-3 text-xs font-extrabold ${priceComparison.summaryClassName}`}>
                        {priceComparison.summaryText}
                        {priceComparison.detailText ? ` (${priceComparison.detailText})` : ''}
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm font-medium text-text-muted">가격 비교 데이터가 부족합니다.</p>
                  )}
                  {priceMetricList.length > 0 && (
                    <ul className="space-y-2">
                      {priceMetricList.map((metric) => (
                        <li
                          key={metric.code}
                          className="rounded-xl border border-light-gray bg-surface-muted/40 px-3 py-2 text-sm font-medium text-eel/80"
                        >
                          {toDisplayMetricLabel(metric.label)}: {metric.value}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="space-y-3 rounded-2xl border border-light-gray bg-white p-4">
                  <p className="text-sm font-black text-eel">재무 건전성</p>
                  <p className="text-xs font-bold text-text-muted">
                    상태: {getXaiSectionStatusLabel(xaiEvaluation.financialEvaluation.status)}
                  </p>
                  <div className="group rounded-xl border border-light-gray bg-surface-muted/40 p-3 transition-all hover:-translate-y-0.5 hover:shadow-sm">
                    <p className="text-xs font-black uppercase tracking-widest text-text-subtle">
                      세이브박스 잔액
                    </p>
                    <p className="mt-1 break-all text-2xl font-black tracking-tight text-eel">
                      {saveboxBalanceLabel}
                    </p>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-light-gray">
                      <div
                        className="h-full rounded-full bg-primary-blue transition-all duration-700"
                        style={{ width: `${saveboxBarPercent}%` }}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-xl border border-light-gray bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-sm">
                      <p className="text-[11px] font-black text-text-subtle">이번 달 고정지출</p>
                      <p className="mt-1 break-all text-lg font-black text-danger">{fixedExpenseLabel}</p>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-light-gray">
                        <div
                          className="h-full rounded-full bg-danger transition-all duration-700"
                          style={{ width: `${fixedExpenseBarPercent}%` }}
                        />
                      </div>
                    </div>
                    <div className="rounded-xl border border-light-gray bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-sm">
                      <p className="text-[11px] font-black text-text-subtle">이번 달 고정 수입</p>
                      <p className="mt-1 break-all text-lg font-black text-success">{fixedIncomeLabel}</p>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-light-gray">
                        <div
                          className="h-full rounded-full bg-success transition-all duration-700"
                          style={{ width: `${fixedIncomeBarPercent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-xl border border-light-gray bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-sm">
                      <p className="text-[11px] font-black text-text-subtle">카드 결제일</p>
                      <p className="mt-1 text-2xl font-black text-danger">{dueDayBadge}</p>
                    </div>
                    <div className="rounded-xl border border-light-gray bg-white p-3 transition-all hover:-translate-y-0.5 hover:shadow-sm">
                      <p className="text-[11px] font-black text-text-subtle">이번 달 카드지출 합계</p>
                      <p className="mt-1 break-all text-lg font-black text-eel">{cardSpendLabel}</p>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-light-gray">
                        <div
                          className="h-full rounded-full bg-accent transition-all duration-700"
                          style={{ width: `${cardSpendBarPercent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-light-gray bg-surface-muted/40 px-3 py-2 text-xs font-bold">
                    <span className="text-text-subtle">월간 수지</span>
                    <span className={monthlyCashflowToneClass}>{monthlyCashflowLabel}</span>
                  </div>
                </div>

                <div className="space-y-2 rounded-2xl border border-light-gray bg-white p-4">
                  <p className="text-sm font-black text-eel">주요 판단 요인</p>
                  {majorTopFactors.length > 0 ? (
                    <ul className="space-y-2">
                      {majorTopFactors.map((factor, index) => (
                        <li
                          key={factor.code}
                          className="rounded-xl border border-light-gray bg-surface-muted/40 px-3 py-2"
                        >
                          <p className="text-sm font-semibold leading-relaxed text-eel/90">
                            <span className="mr-2 text-primary-blue">{String(index + 1).padStart(2, '0')}</span>
                            {factor.label}
                          </p>
                          <p className="mt-1 text-xs font-black text-primary-blue">
                            영향도 {formatImpactPercent(factor.impact)}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm font-medium text-text-muted">상위 판단 요인이 아직 없습니다.</p>
                  )}
                </div>

                <div className="space-y-2 rounded-2xl border border-light-gray bg-white p-4">
                  <p className="text-sm font-black text-eel">근거 데이터</p>
                  {xaiEvaluation.supportingEvidence.length > 0 ? (
                    <ul className="space-y-2">
                      {xaiEvaluation.supportingEvidence.map((evidence) => (
                        <li
                          key={`${evidence.field}-${evidence.snapshotId ?? evidence.source}`}
                          className="rounded-xl border border-light-gray bg-surface-muted/40 px-3 py-2 text-sm font-medium text-eel/80"
                        >
                          {getXaiEvidenceFieldLabel(evidence.field)}:{' '}
                          {formatXaiEvidenceValue(evidence.field, evidence.value)} ·{' '}
                          {getXaiEvidenceSourceLabel(evidence.source)}
                          {(evidence.isDefault || evidence.isEstimated) && (
                            <span className="ml-2 text-xs font-bold text-amber-600">
                              {evidence.isEstimated ? '추정값' : '기본값'}
                            </span>
                          )}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm font-medium text-text-muted">노출할 근거 데이터가 없습니다.</p>
                  )}
                </div>

                {xaiEvaluation.decision.trim().toUpperCase() !== 'BUY_NOW' && (
                  <div className="space-y-2 rounded-2xl border border-light-gray bg-white p-4">
                    <p className="text-sm font-black text-eel">Counterfactual</p>
                    {xaiEvaluation.counterfactuals.length > 0 ? (
                      <ul className="space-y-2">
                        {xaiEvaluation.counterfactuals.map((counterfactual) => (
                          <li
                            key={`${counterfactual.label}-${counterfactual.targetDecision}`}
                            className="rounded-xl border border-light-gray bg-surface-muted/40 px-3 py-2 text-sm font-medium text-eel/80"
                          >
                            {counterfactual.label}
                            <span className="ml-2 text-xs font-bold text-primary-blue">
                              →{' '}
                              {decisionLabelMap[counterfactual.targetDecision] ??
                                counterfactual.targetDecision}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm font-medium text-text-muted">counterfactual이 아직 없습니다.</p>
                    )}
                  </div>
                )}

                {xaiEvaluation.warnings.length > 0 && (
                  <div className="space-y-2 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                    <p className="text-sm font-black text-amber-700">주의 사항</p>
                    <ul className="space-y-2">
                      {xaiEvaluation.warnings.map((warning) => (
                        <li key={warning} className="text-sm font-semibold text-amber-700">
                          {getXaiWarningLabel(warning)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm font-medium text-text-muted">
                  아직 XAI 판단 결과를 조회하지 않았습니다.
                </p>
                {isXaiAvailabilityLoading ? (
                  <p className="text-xs font-semibold text-text-subtle">
                    XAI 활성화 가능 여부를 확인 중입니다.
                  </p>
                ) : (
                  <p className="text-xs font-semibold text-text-subtle">
                    {xaiAvailability?.reason ?? 'XAI 활성화 상태 정보가 없습니다.'}
                  </p>
                )}
                <Button
                  type="button"
                  className="!w-auto !rounded-xl !px-4 !py-2 !text-xs"
                  disabled={
                    isXaiAvailabilityLoading ||
                    !xaiAvailability?.enabled ||
                    (hasRequestedXai && isXaiLoading)
                  }
                  onClick={() => void handleFetchXaiEvaluation()}
                >
                  XAI 판단 보기
                </Button>
              </div>
            )}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border-light-gray shadow-xl">
          <div className="flex items-center justify-between border-b border-light-gray bg-surface-muted/50 px-6 py-5">
            <h3 className="text-xl font-black text-eel tracking-tight">투표 현황</h3>
            <span className="text-xs font-black text-text-subtle uppercase px-2 py-1 bg-white border border-light-gray rounded-lg">{detail.totalVoteCount} Members</span>
          </div>
          <div className="p-6 space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-[11px] font-black uppercase tracking-widest">
                <span className="text-success">Agree</span>
                <span className="text-danger">Reject</span>
              </div>
              <div className="h-5 flex overflow-hidden rounded-full bg-light-gray shadow-inner p-0.5 ring-1 ring-light-gray">
                {detail.totalVoteCount > 0 ? (
                  <>
                    {detail.agreeCount > 0 && (
                      <div
                        className={`h-full bg-success transition-all duration-1000 flex items-center justify-center ${detail.disagreeCount === 0 ? 'rounded-full' : 'rounded-l-full'}`}
                        style={{ width: `${agreeRatio}%` }}
                      >
                        {agreeRatio > 15 && <span className="text-[9px] font-black text-white/80">{Math.round(agreeRatio)}%</span>}
                      </div>
                    )}
                    {detail.disagreeCount > 0 && (
                      <div
                        className={`h-full bg-danger transition-all duration-1000 flex items-center justify-center ${detail.agreeCount === 0 ? 'rounded-full' : 'rounded-r-full'} ${detail.agreeCount > 0 ? 'border-l-2 border-white/20' : ''}`}
                        style={{ width: `${100 - agreeRatio}%` }}
                      >
                        {(100 - agreeRatio) > 15 && <span className="text-[9px] font-black text-white/80">{Math.round(100 - agreeRatio)}%</span>}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="h-full w-full bg-gray-200/50 flex items-center justify-center">
                    <span className="text-[9px] font-black text-text-subtle uppercase tracking-widest">Pending Votes</span>
                  </div>
                )}
              </div>
              <div className="flex justify-between items-end">
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-success tracking-tighter">{detail.agreeCount}</span>
                  <span className="text-[11px] font-bold text-success/60">표</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-black text-danger tracking-tighter">{detail.disagreeCount}</span>
                  <span className="text-[11px] font-bold text-danger/60">표</span>
                </div>
              </div>
            </div>

            {canVote ? (
              <div className="space-y-4 pt-2 border-t border-light-gray">
                <textarea
                  className="min-h-[100px] w-full rounded-2xl border-2 border-light-gray bg-surface-muted/30 px-4 py-3 text-sm font-medium outline-none focus:border-accent-soft focus:bg-white focus:ring-4 focus:ring-accent-soft/20 transition-all resize-none"
                  placeholder="의견을 남겨주시면 큰 도움이 됩니다구루! (선택사항)"
                  value={voteOpinion}
                  onChange={(event) => setVoteOpinion(event.target.value)}
                  disabled={isSubmittingVote}
                  maxLength={1000}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    type="button"
                    className="!bg-none !bg-success !py-4 !rounded-2xl shadow-[0_4px_12px_rgba(21,128,61,0.2)] hover:shadow-[0_8px_16px_rgba(21,128,61,0.3)] transition-all"
                    onClick={() => void handleVote('AGREE')}
                    disabled={isSubmittingVote}
                  >
                    APPROVE
                  </Button>
                  <Button
                    type="button"
                    className="!bg-none !bg-danger !py-4 !rounded-2xl shadow-[0_4px_12px_rgba(225,29,72,0.2)] hover:shadow-[0_8px_16px_rgba(225,29,72,0.3)] transition-all"
                    onClick={() => void handleVote('DISAGREE')}
                    disabled={isSubmittingVote}
                  >
                    REJECT
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border-2 border-dashed border-light-gray bg-surface-muted/50 p-5 text-center">
                <p className="text-xs font-black text-text-subtle uppercase tracking-widest mb-1">Voting Disabled</p>
                <p className="text-sm font-bold text-text-muted leading-tight">{voteDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>

        {canClose && (
          <Card className="!p-0 overflow-hidden border-light-gray shadow-xl bg-eel/5 ring-1 ring-eel/10">
            <div className="border-b border-light-gray/20 bg-eel/10 px-6 py-5">
              <h3 className="text-xl font-black text-eel tracking-tight">최종 상태 결정</h3>
            </div>
            <div className="p-6 space-y-5">
              <p className="text-[11px] font-bold text-text-muted leading-relaxed text-center px-4">
                이 구매 요청의 최종 수락 여부를 결정합니다. <br/>결정 후에는 내용을 수정하거나 투표를 받을 수 없습니다.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <Button
                  type="button"
                  className="!bg-none !bg-success !py-4 !rounded-2xl shadow-[0_8px_20px_rgba(21,128,61,0.2)] hover:shadow-[0_12px_28px_rgba(21,128,61,0.3)] transition-all"
                  onClick={() => void handleClosePr('MERGED')}
                  disabled={isClosingPr}
                >
                  MERGE
                </Button>
                <Button
                  type="button"
                  className="!bg-none !bg-danger !py-4 !rounded-2xl shadow-[0_8px_20px_rgba(225,29,72,0.2)] hover:shadow-[0_12px_28px_rgba(225,29,72,0.3)] transition-all"
                  onClick={() => void handleClosePr('CLOSED')}
                  disabled={isClosingPr}
                >
                  CLOSE
                </Button>
              </div>
            </div>
          </Card>
        )}
      </aside>
    </div>
  );
};
