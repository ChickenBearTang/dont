import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Card } from '@/shared/components';
import { closePr, getPrDetail, submitPrVote } from '@/features/community/pr';
import type { PrDetailResponseData } from '@/features/community/pr';
import { useUIStore } from '@/shared/store/useUIStore';
import { formatRelativeTime } from '@/shared/utils/date';

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

const getStatusBadgeClass = (status: string): string => {
  const normalizedStatus = normalizePrStatus(status);

  if (normalizedStatus === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (normalizedStatus === 'MERGED') return 'bg-green-50 text-green-700 border-green-200';
  if (normalizedStatus === 'CLOSED') return 'bg-rose-50 text-rose-700 border-rose-200';
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

const getTimelineDotClass = (type: 'base' | 'review' | 'status'): string => {
  if (type === 'review') return 'bg-emerald-500';
  if (type === 'status') return 'bg-violet-500';
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
  const closeDisabledReason = detail.permissions?.closeDisabledReason ?? 'PR을 종료할 수 없습니다.';
  const agreeRatio =
    detail.totalVoteCount > 0 ? (detail.agreeCount / detail.totalVoteCount) * 100 : 0;
  const timelineEvents = buildTimelineEvents(detail);
  const contentSections = parseContentSections(detail.content);
  const latestEventTime =
    detail.events && detail.events.length > 0
      ? detail.events[detail.events.length - 1].createdAt
      : detail.closedAt ?? detail.updatedAt;

  return (
    <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full border px-3.5 py-1 text-sm font-bold ${getStatusBadgeClass(detail.status)}`}
              >
                {normalizePrStatus(detail.status)}
              </span>
              <span className="text-sm font-semibold text-gray-500">PR #{detail.postId}</span>
            </div>
            <h1 className="text-[32px] font-black leading-tight text-gray-900">{detail.title}</h1>
            <p className="text-sm font-medium text-gray-500">
              {detail.authorNickname} · 작성 {formatAbsoluteDate(detail.createdAt)}
              {detail.updatedAt !== detail.createdAt
                ? ` · 수정 ${formatAbsoluteDate(detail.updatedAt)}`
                : ''}
            </p>
          </div>
          <button
            type="button"
            className="rounded-2xl border border-gray-300 px-5 py-2.5 text-sm font-bold text-gray-700 transition-colors hover:bg-gray-50"
            onClick={() => navigate('/community/write?category=PR')}
          >
            글쓰기
          </button>
        </div>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="flex items-center justify-between gap-3 border-b border-gray-200 px-7 py-5">
            <div>
              <p className="text-[31px] font-black leading-none text-gray-900">{detail.itemName}</p>
              <p className="mt-2 text-sm font-semibold text-gray-500">
                최근 업데이트 {latestEventTime ? formatRelativeTime(latestEventTime) : '-'}
              </p>
            </div>
            {detail.deadlineAt ? (
              <span className="shrink-0 rounded-full border border-slate-200 bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700">
                마감 {formatDateTime(detail.deadlineAt)}
              </span>
            ) : null}
          </div>

          <div className="grid grid-cols-1 gap-3 border-b border-gray-200 bg-gradient-to-r from-slate-50 to-blue-50/40 px-7 py-5 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-100/80 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">요청 금액</p>
              <p className="mt-1 text-[28px] font-black leading-none text-gray-900">
                {formatCurrency(detail.priceAmount)}
              </p>
            </div>
            <div className="rounded-2xl bg-emerald-50 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">Approve</p>
              <p className="mt-1 text-[28px] font-black leading-none text-emerald-700">
                {detail.agreeCount}표
              </p>
            </div>
            <div className="rounded-2xl bg-rose-50 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">Reject</p>
              <p className="mt-1 text-[28px] font-black leading-none text-rose-700">
                {detail.disagreeCount}표
              </p>
            </div>
          </div>

          <div className="space-y-5 px-7 py-6">
            {contentSections.map((section) => (
              <div key={section.title} className="space-y-2">
                <h2 className="text-[18px] font-black text-gray-900">{section.title}</h2>
                <p className="whitespace-pre-wrap text-[16px] leading-relaxed text-gray-800">
                  {section.body || '내용이 없습니다.'}
                </p>
              </div>
            ))}
            <p className="text-sm font-semibold text-gray-600">카테고리: {detail.category ?? '-'}</p>
          </div>
        </Card>

        <div className="relative space-y-4 pl-10">
          <div className="absolute bottom-3 left-4 top-3 w-px bg-gradient-to-b from-blue-200 via-gray-200 to-violet-200" />
          {timelineEvents.map((event) => (
            <div key={event.id} className="relative">
              <span
                className={`absolute -left-[30px] top-5 h-4 w-4 rounded-full border-[3px] border-white shadow-md ${getTimelineDotClass(event.type)}`}
              />
              <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
                <div className="flex items-center justify-between gap-3 border-b border-gray-200 bg-gray-50/70 px-5 py-3.5">
                  <p className="text-base font-black text-gray-900">
                    {event.title}
                    {event.actorLabel ? (
                      <span className="ml-2 text-xs font-semibold text-gray-500">
                        {event.actorLabel}
                      </span>
                    ) : null}
                  </p>
                  <span className="shrink-0 text-xs font-semibold text-gray-500">
                    {event.timeLabel}
                  </span>
                </div>
                <div className="space-y-2.5 px-5 py-4">
                  <p className="text-sm font-bold text-gray-600">{event.subTitle}</p>
                  <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-gray-800">
                    {event.content}
                  </p>
                </div>
              </Card>
            </div>
          ))}
        </div>

        {detail.reviews && detail.reviews.length > 0 ? (
          <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
            <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3.5">
              <h3 className="text-lg font-black text-gray-900">리뷰 코멘트</h3>
              <span className="text-xs font-semibold text-gray-500">{detail.reviews.length}건</span>
            </div>
            <div className="divide-y divide-gray-100">
              {detail.reviews.map((review) => (
                <div key={review.reviewId} className="space-y-1.5 px-5 py-4">
                  <div className="flex items-center gap-2">
                    {review.userProfileImageUrl ? (
                      <img
                        src={review.userProfileImageUrl}
                        alt={review.userNickname ?? `사용자 ${review.userId}`}
                        className="h-7 w-7 rounded-full border border-gray-200 object-cover"
                      />
                    ) : (
                      <div className="h-7 w-7 rounded-full border border-gray-200 bg-gray-100" />
                    )}
                    <p className="text-sm font-bold text-gray-900">
                      {review.decision === 'APPROVE' ? 'Approve' : 'Reject'} ·{' '}
                      {review.userNickname ?? `사용자 #${review.userId}`}
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">{formatRelativeTime(review.createdAt)}</p>
                  <p className="text-sm text-gray-700">
                    {review.content && review.content.trim().length > 0
                      ? review.content
                      : '의견 없이 결정만 등록했습니다.'}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        ) : null}

        {!isOpen && (
          <Card className="border border-slate-200 bg-slate-50 py-10 text-center hover:!translate-y-0">
            <h3 className="text-[32px] font-black leading-none text-gray-900">
              이 구매 요청은 {detail.status} 되었습니다.
            </h3>
            <p className="mt-3 font-medium text-gray-500">
              결정이 완료되어 더 이상 리뷰를 남길 수 없습니다.
            </p>
          </Card>
        )}
      </section>

      <aside className="space-y-4 xl:sticky xl:top-24">
        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="border-b border-gray-200 px-5 py-3.5">
            <h3 className="text-[30px] font-black leading-none text-gray-900">대상 상품</h3>
          </div>
          <div className="space-y-3.5 p-5">
            {detail.imageUrl ? (
              <img
                src={detail.imageUrl}
                alt={detail.itemName}
                className="h-48 w-full rounded-2xl border border-gray-200 object-cover"
              />
            ) : (
              <div className="flex h-48 w-full items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-gray-50 text-base font-bold text-gray-400">
                이미지 없음
              </div>
            )}
            <p className="text-[22px] font-black leading-snug text-gray-900">{detail.itemName}</p>
            <p className="text-[42px] font-black leading-none tracking-tight text-gray-900">
              {formatCurrency(detail.priceAmount)}
            </p>
            {detail.deadlineAt ? (
              <p className="text-sm font-semibold text-gray-500">
                투표 마감 {formatDateTime(detail.deadlineAt)}
              </p>
            ) : null}
            {detail.purchaseUrl ? (
              <a
                href={detail.purchaseUrl}
                target="_blank"
                rel="noreferrer"
                className="block rounded-xl bg-[#101934] py-3.5 text-center text-[22px] font-black text-white transition-colors hover:bg-[#1a2341]"
              >
                구매처에서 보기
              </a>
            ) : (
              <p className="text-sm text-gray-500">구매 링크 없음</p>
            )}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3.5">
            <h3 className="text-[30px] font-black leading-none text-gray-900">리뷰어 투표 현황</h3>
            <span className="text-sm font-bold text-gray-700">{detail.totalVoteCount}명 참여</span>
          </div>
          <div className="space-y-4 p-5">
            <div className="h-3 overflow-hidden rounded-full bg-gray-100">
              <div className="h-full bg-emerald-500" style={{ width: `${agreeRatio}%` }} />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xl">
              <p className="font-black text-emerald-700">Approve {detail.agreeCount}</p>
              <p className="font-black text-red-700">Reject {detail.disagreeCount}</p>
              <p className="font-black text-gray-900">총 {detail.totalVoteCount}</p>
            </div>

            {canVote ? (
              <>
                <textarea
                  className="min-h-[90px] w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-primary-blue"
                  placeholder="의견을 남겨주세요 (선택)"
                  value={voteOpinion}
                  onChange={(event) => setVoteOpinion(event.target.value)}
                  disabled={isSubmittingVote}
                  maxLength={1000}
                />
                <div className="grid grid-cols-2 gap-2.5">
                  <Button
                    type="button"
                    className="!bg-green-600 !py-2.5 text-xl hover:!bg-green-700 disabled:!bg-gray-300"
                    onClick={() => void handleVote('AGREE')}
                    disabled={isSubmittingVote}
                  >
                    Approve
                  </Button>
                  <Button
                    type="button"
                    className="!bg-red-600 !py-2.5 text-xl hover:!bg-red-700 disabled:!bg-gray-300"
                    onClick={() => void handleVote('DISAGREE')}
                    disabled={isSubmittingVote}
                  >
                    Reject
                  </Button>
                </div>
              </>
            ) : (
              <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5">
                <p className="text-xs font-semibold text-gray-500">{voteDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="border-b border-gray-200 px-5 py-3.5">
            <h3 className="text-[30px] font-black leading-none text-gray-900">PR 종료</h3>
          </div>
          <div className="space-y-3.5 p-5">
            <p className="text-xs font-medium text-gray-500">
              다른 사용자의 투표는 참고용이며, 최종 상태는 작성자만 결정할 수 있습니다.
            </p>
            {canClose ? (
              <div className="grid grid-cols-2 gap-2.5">
                <Button
                  type="button"
                  className="!bg-emerald-600 !py-2.5 text-xl hover:!bg-emerald-700 disabled:!bg-gray-300"
                  onClick={() => void handleClosePr('MERGED')}
                  disabled={isClosingPr}
                >
                  MERGED
                </Button>
                <Button
                  type="button"
                  className="!bg-slate-600 !py-2.5 text-xl hover:!bg-slate-700 disabled:!bg-gray-300"
                  onClick={() => void handleClosePr('CLOSED')}
                  disabled={isClosingPr}
                >
                  CLOSED
                </Button>
              </div>
            ) : (
              <div className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2.5">
                <p className="text-xs font-semibold text-gray-500">{closeDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>
      </aside>
    </div>
  );
};
