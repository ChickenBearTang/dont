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

const getStatusBadgeClass = (status: string): string => {
  if (status === 'OPEN') return 'bg-blue-50 text-blue-700 border-blue-200';
  if (status === 'MERGED') return 'bg-green-50 text-green-700 border-green-200';
  return 'bg-gray-100 text-gray-700 border-gray-200';
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

const parseEventPayload = (payload: Record<string, unknown> | null): EventPayload => {
  if (!payload) return {};

  return payload as EventPayload;
};

const buildTimelineEvents = (detail: PrDetailResponseData): TimelineEvent[] => {
  if (detail.events && detail.events.length > 0) {
    return detail.events.map((event) => {
      const payload = parseEventPayload(event.payload);

      if (event.eventType === 'REVIEW_SUBMITTED') {
        return {
          id: `event-${event.eventId}`,
          type: 'review',
          title: '리뷰 제출',
          subTitle: payload.decision ? `결정: ${payload.decision}` : '리뷰가 등록되었습니다.',
          content:
            payload.opinionText && payload.opinionText.trim().length > 0
              ? payload.opinionText
              : `리뷰어 #${event.actorUserId ?? '-'}가 의견을 남겼습니다.`,
          timeLabel: formatRelativeTime(event.createdAt),
          actorLabel: event.actorNickname ?? null,
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
          actorLabel: event.actorNickname ?? null,
        };
      }

      return {
        id: `event-${event.eventId}`,
        type: 'base',
        title: '구매 요청 생성',
        subTitle: `카테고리: ${detail.category ?? '미지정'}`,
        content:
          payload.title && payload.itemName
            ? `${payload.title} / ${payload.itemName}`
            : detail.content,
        timeLabel: formatRelativeTime(event.createdAt),
        actorLabel: event.actorNickname ?? null,
      };
    });
  }

  return [
    {
      id: 'base-fallback',
      type: 'base',
      title: '구매 요청 생성',
      subTitle: `카테고리: ${detail.category ?? '미지정'}`,
      content: detail.content,
      timeLabel: '요청 등록',
    },
    ...(detail.totalVoteCount > 0
      ? [
          {
            id: 'review-fallback',
            type: 'review' as const,
            title: '리뷰 투표 집계',
            subTitle: `찬성 ${detail.agreeCount} / 반대 ${detail.disagreeCount}`,
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
            subTitle: `결과: ${detail.resultStatus ?? detail.status}`,
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
      <Card className="flex flex-col items-center gap-4 text-center py-12">
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
  const latestEventTime =
    detail.events && detail.events.length > 0
      ? detail.events[detail.events.length - 1].createdAt
      : detail.closedAt;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-6 items-start">
      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h1 className="text-[38px] font-black text-gray-900 leading-none">
              Purchase Request #{detail.postId}
            </h1>
            <span
              className={`px-3.5 py-1 rounded-full border text-sm font-bold ${getStatusBadgeClass(detail.status)}`}
            >
              {detail.status}
            </span>
          </div>
          <button
            type="button"
            className="px-5 py-2.5 rounded-2xl border border-gray-300 text-sm font-bold text-gray-700 hover:bg-gray-50 transition-colors"
            onClick={() => navigate('/community/pr/new')}
          >
            New PR
          </button>
        </div>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="px-7 py-5 border-b border-gray-200 flex items-center justify-between gap-3">
            <div>
              <p className="text-[31px] font-black text-gray-900 leading-none">{detail.itemName}</p>
              <p className="text-sm text-gray-500 font-semibold mt-2">
                최근 업데이트 {latestEventTime ? formatRelativeTime(latestEventTime) : '-'}
              </p>
            </div>
            <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-100 shrink-0">
              마이데이터 연동됨
            </span>
          </div>

          <div className="px-7 py-5 border-b border-gray-200 grid grid-cols-1 md:grid-cols-3 gap-3 bg-gradient-to-r from-slate-50 to-blue-50/40">
            <div className="rounded-2xl bg-slate-100/80 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">요청 금액</p>
              <p className="text-[28px] font-black text-gray-900 mt-1 leading-none">
                {formatCurrency(detail.priceAmount)}
              </p>
            </div>
            <div className="rounded-2xl bg-emerald-50 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">현재 찬성</p>
              <p className="text-[28px] font-black text-emerald-700 mt-1 leading-none">
                {detail.agreeCount}표
              </p>
            </div>
            <div className="rounded-2xl bg-violet-50 px-4 py-3.5">
              <p className="text-xs font-bold text-gray-500">전체 투표</p>
              <p className="text-[28px] font-black text-violet-700 mt-1 leading-none">
                {detail.totalVoteCount}표
              </p>
            </div>
          </div>

          <div className="px-7 py-6 space-y-3">
            <p className="text-[17px] leading-relaxed text-gray-800 whitespace-pre-wrap">
              {detail.content}
            </p>
            <p className="text-sm font-semibold text-gray-600">
              카테고리: {detail.category ?? '-'}
            </p>
          </div>
        </Card>

        <div className="relative pl-10 space-y-4">
          <div className="absolute left-4 top-3 bottom-3 w-px bg-gradient-to-b from-blue-200 via-gray-200 to-violet-200" />
          {timelineEvents.map((event) => (
            <div key={event.id} className="relative">
              <span
                className={`absolute -left-[30px] top-5 w-4 h-4 rounded-full border-[3px] border-white shadow-md ${getTimelineDotClass(event.type)}`}
              />
              <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
                <div className="px-5 py-3.5 border-b border-gray-200 bg-gray-50/70 flex items-center justify-between gap-3">
                  <p className="text-base font-black text-gray-900">
                    {event.title}
                    {event.actorLabel ? (
                      <span className="ml-2 text-xs font-semibold text-gray-500">
                        {event.actorLabel}
                      </span>
                    ) : null}
                  </p>
                  <span className="text-xs font-semibold text-gray-500 shrink-0">
                    {event.timeLabel}
                  </span>
                </div>
                <div className="px-5 py-4 space-y-2.5">
                  <p className="text-sm font-bold text-gray-600">{event.subTitle}</p>
                  <p className="text-[15px] leading-relaxed text-gray-800 whitespace-pre-wrap">
                    {event.content}
                  </p>
                </div>
              </Card>
            </div>
          ))}
        </div>

        {detail.reviews && detail.reviews.length > 0 ? (
          <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
            <div className="px-5 py-3.5 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-black text-gray-900">리뷰 코멘트</h3>
              <span className="text-xs font-semibold text-gray-500">{detail.reviews.length}건</span>
            </div>
            <div className="divide-y divide-gray-100">
              {detail.reviews.map((review) => (
                <div key={review.reviewId} className="px-5 py-4 space-y-1.5">
                  <div className="flex items-center gap-2">
                    {review.userProfileImageUrl ? (
                      <img
                        src={review.userProfileImageUrl}
                        alt={review.userNickname ?? `사용자 ${review.userId}`}
                        className="w-7 h-7 rounded-full object-cover border border-gray-200"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-full bg-gray-100 border border-gray-200" />
                    )}
                    <p className="text-sm font-bold text-gray-900">
                      {review.decision} · {review.userNickname ?? `사용자 #${review.userId}`}
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
          <Card className="text-center py-10 hover:!translate-y-0 bg-slate-50 border border-slate-200">
            <h3 className="text-[32px] font-black text-gray-900 leading-none">
              이 구매 요청은 {detail.status} 되었습니다.
            </h3>
            <p className="text-gray-500 font-medium mt-3">
              결정이 완료되어 더 이상 리뷰를 남길 수 없습니다.
            </p>
          </Card>
        )}
      </section>

      <aside className="space-y-4 xl:sticky xl:top-24">
        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="px-5 py-3.5 border-b border-gray-200">
            <h3 className="text-[30px] font-black text-gray-900 leading-none">대상 핫딜</h3>
          </div>
          <div className="p-5 space-y-3.5">
            {detail.imageUrl ? (
              <img
                src={detail.imageUrl}
                alt={detail.itemName}
                className="w-full h-48 object-cover rounded-2xl border border-gray-200"
              />
            ) : (
              <div className="w-full h-48 rounded-2xl border border-dashed border-gray-300 bg-gray-50 flex items-center justify-center text-base font-bold text-gray-400">
                이미지 없음
              </div>
            )}
            <p className="font-black text-[22px] text-gray-900 leading-snug">{detail.itemName}</p>
            <p className="text-[42px] font-black text-gray-900 tracking-tight leading-none">
              {formatCurrency(detail.priceAmount)}
            </p>
            {detail.purchaseUrl ? (
              <a
                href={detail.purchaseUrl}
                target="_blank"
                rel="noreferrer"
                className="block text-center rounded-xl bg-[#101934] text-white text-[22px] font-black py-3.5 hover:bg-[#1a2341] transition-colors"
              >
                구매처에서 보기
              </a>
            ) : (
              <p className="text-sm text-gray-500">구매 링크 없음</p>
            )}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="px-5 py-3.5 border-b border-gray-200 flex items-center justify-between">
            <h3 className="text-[30px] font-black text-gray-900 leading-none">리뷰어 투표 현황</h3>
            <span className="text-sm font-bold text-gray-700">{detail.totalVoteCount}명 참여</span>
          </div>
          <div className="p-5 space-y-4">
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: `${agreeRatio}%` }} />
            </div>
            <div className="grid grid-cols-3 gap-2 text-xl">
              <p className="font-black text-emerald-700">찬성 {detail.agreeCount}</p>
              <p className="font-black text-red-700">반대 {detail.disagreeCount}</p>
              <p className="font-black text-gray-900">총 {detail.totalVoteCount}</p>
            </div>

            {canVote ? (
              <>
                <textarea
                  className="w-full min-h-[90px] rounded-xl border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-primary-blue"
                  placeholder="의견을 남겨주세요 (선택)"
                  value={voteOpinion}
                  onChange={(event) => setVoteOpinion(event.target.value)}
                  disabled={isSubmittingVote}
                  maxLength={1000}
                />
                <div className="grid grid-cols-2 gap-2.5">
                  <Button
                    type="button"
                    className="!py-2.5 text-xl !bg-green-600 hover:!bg-green-700 disabled:!bg-gray-300"
                    onClick={() => void handleVote('AGREE')}
                    disabled={isSubmittingVote}
                  >
                    Approve
                  </Button>
                  <Button
                    type="button"
                    className="!py-2.5 text-xl !bg-red-600 hover:!bg-red-700 disabled:!bg-gray-300"
                    onClick={() => void handleVote('DISAGREE')}
                    disabled={isSubmittingVote}
                  >
                    Reject
                  </Button>
                </div>
              </>
            ) : (
              <div className="rounded-xl bg-gray-50 border border-gray-200 px-3 py-2.5">
                <p className="text-xs text-gray-500 font-semibold">{voteDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>

        <Card className="!p-0 overflow-hidden border border-gray-200 hover:!translate-y-0">
          <div className="px-5 py-3.5 border-b border-gray-200">
            <h3 className="text-[30px] font-black text-gray-900 leading-none">PR 종료</h3>
          </div>
          <div className="p-5 space-y-3.5">
            <p className="text-xs text-gray-500 font-medium">
              작성자만 PR을 종료할 수 있으며, 권한은 서버에서 검증됩니다.
            </p>
            {canClose ? (
              <div className="grid grid-cols-2 gap-2.5">
                <Button
                  type="button"
                  className="!py-2.5 text-xl !bg-emerald-600 hover:!bg-emerald-700 disabled:!bg-gray-300"
                  onClick={() => void handleClosePr('MERGED')}
                  disabled={isClosingPr}
                >
                  MERGED
                </Button>
                <Button
                  type="button"
                  className="!py-2.5 text-xl !bg-slate-600 hover:!bg-slate-700 disabled:!bg-gray-300"
                  onClick={() => void handleClosePr('CLOSED')}
                  disabled={isClosingPr}
                >
                  CLOSED
                </Button>
              </div>
            ) : (
              <div className="rounded-xl bg-gray-50 border border-gray-200 px-3 py-2.5">
                <p className="text-xs text-gray-500 font-semibold">{closeDisabledReason}</p>
              </div>
            )}
          </div>
        </Card>
      </aside>
    </div>
  );
};
