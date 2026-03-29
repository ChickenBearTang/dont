import { useEffect, useState, useMemo, useRef } from 'react';
import type { Dispatch, FormEvent, SetStateAction } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  createComment,
  deleteComment,
  deletePost,
  getCommentReplies,
  getHotdealDetail,
  getComments,
  getPollDetail,
  getPost,
  submitPollVote,
  toggleReaction,
  updateComment,
} from '../api/communityApi';
import type {
  BoardCategory,
  CommentReplyDto,
  CommentThreadDto,
  GetPostResponseDto,
  HotdealDetailResponseDto,
  PollDetailResponseDto,
  ReactionType,
  ReportTargetType,
} from '../types';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useUIStore } from '@/shared/store/useUIStore';
import { ReportModal } from '../components/ReportModal';
import { Modal } from '@/shared/components/Modal';
import { UserAvatar } from '../components/UserAvatar';
import { LinkifiedText } from '../components/LinkifiedText';
import { Card, Button } from '@/shared/components';

const getStatusLabelWithEmoji = (status: string | undefined): string => {
  const normalized = status?.trim().toUpperCase();
  if (normalized === 'OPEN' || normalized === 'LIVE') return '📂 OPEN';
  if (normalized === 'CLOSED' || normalized === 'EXPIRED') return '🚫 CLOSED';
  if (normalized === 'MERGED') return '✔️ MERGED';
  return status ?? 'OPEN';
};

const COMMENT_PAGE_SIZE = 10;
const REPLY_PAGE_SIZE = 10;
const COMMENT_SCROLL_OFFSET = 72;

type CommentEntryDto = CommentThreadDto | CommentReplyDto;
type ThreadReplyLoadState = {
  replies: CommentReplyDto[];
  repliesLoaded: boolean;
  repliesLoading: boolean;
  repliesPage: number;
  repliesHasNext: boolean;
};
type CommentThreadView = CommentThreadDto & ThreadReplyLoadState;

interface CommentEntryProps {
  comment: CommentEntryDto;
  currentUser: ReturnType<typeof useAuthStore.getState>['user'];
  handleDeleteComment: (id: number) => void;
  onNavigateToComment: (commentId: number) => void;
  onActivateComment?: () => void;
  onDeactivateComment?: () => void;
  postId: string | undefined;
  refreshComments: (fetchAll?: boolean) => Promise<void>;
  refreshReplies: (rootCommentId: number) => Promise<void>;
  rootCommentId: number;
  setPost: Dispatch<SetStateAction<GetPostResponseDto | null>>;
  formatDate: (dateStr: string) => string;
  onReport: (type: ReportTargetType, id: number) => void;
  highlightedCommentId: number | null;
  nested?: boolean;
}

interface CommentThreadItemProps extends Omit<CommentEntryProps, 'comment' | 'nested'> {
  thread: CommentThreadView;
  loadInitialReplies: (rootCommentId: number) => Promise<void>;
  loadMoreReplies: (rootCommentId: number) => Promise<void>;
}

interface PollVotePanelProps {
  detail: PollDetailResponseDto;
  selectedVote: 'OPTION_A' | 'OPTION_B' | null;
  isSubmittingVote: boolean;
  onVote: (voteOption: 'OPTION_A' | 'OPTION_B') => void;
}

interface HotdealInfoPanelProps {
  detail: HotdealDetailResponseDto;
}

const CommentEntry = ({
  comment,
  currentUser,
  handleDeleteComment,
  onNavigateToComment,
  onActivateComment,
  onDeactivateComment,
  postId,
  refreshComments,
  refreshReplies,
  rootCommentId,
  setPost,
  formatDate,
  onReport,
  highlightedCommentId,
  nested = false,
}: CommentEntryProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isHighlighted = comment.commentId === highlightedCommentId;

  useEffect(() => {
    if (isHighlighted && containerRef.current) {
      setTimeout(() => {
        containerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 500);
    }
  }, [isHighlighted]);

  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [submittingReply, setSubmittingReply] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [submittingEdit, setSubmittingEdit] = useState(false);

  const commentLikeKey = `comment_like_${comment.commentId}`;
  const [isLiked, setIsLiked] = useState(() => localStorage.getItem(commentLikeKey) === 'true');

  const isCommentAuthor = comment.isMine ?? currentUser?.userId === comment.authorId;
  const replyToNickname = 'replyToNickname' in comment ? comment.replyToNickname : null;
  const replyPlaceholder = `${comment.authorNickname || '알 수 없음'}님에게 답글을 입력하세요...`;

  const handleReplySubmit = async (e: FormEvent) => {
    e.preventDefault();
    const finalContent = replyContent.trim().replace(/\n{3,}/g, '\n\n');
    if (!postId || !finalContent || submittingReply) return;
    setSubmittingReply(true);
    try {
      await createComment(Number(postId), {
        content: finalContent,
        parentCommentId: comment.commentId,
      });
      setReplyContent('');
      setIsReplying(false);
      await refreshComments(true);
      await refreshReplies(rootCommentId);
      setPost((prev) => (prev ? { ...prev, commentCount: prev.commentCount + 1 } : null));
    } catch {
      alert('답글 작성에 실패했습니다.');
    } finally {
      setSubmittingReply(false);
    }
  };

  const handleEditSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const finalContent = editContent.trim().replace(/\n{3,}/g, '\n\n');
    if (!finalContent || submittingEdit) return;
    setSubmittingEdit(true);
    try {
      await updateComment(comment.commentId, { content: finalContent });
      setIsEditing(false);
      await refreshComments(true);
      await refreshReplies(rootCommentId);
    } catch {
      alert('댓글 수정에 실패했습니다.');
    } finally {
      setSubmittingEdit(false);
    }
  };

  const handleToggleCommentReaction = async () => {
    if (comment.status === 'BLINDED') return;
    const nextActive = !isLiked;
    try {
      await toggleReaction({
        targetType: 'COMMENT',
        targetId: comment.commentId,
        reactionType: 'LIKE',
        active: nextActive,
      });
      setIsLiked(nextActive);
      if (nextActive) localStorage.setItem(commentLikeKey, 'true');
      else localStorage.removeItem(commentLikeKey);
      await refreshComments(true);
      await refreshReplies(rootCommentId);
    } catch (err: unknown) {
      const axiosError = err as { response?: { status: number } };
      if (axiosError.response?.status === 400 || axiosError.response?.status === 409) {
        setIsLiked(!isLiked);
        if (!isLiked) localStorage.setItem(commentLikeKey, 'true');
        else localStorage.removeItem(commentLikeKey);
        await refreshComments(true);
        await refreshReplies(rootCommentId);
      } else {
        alert('반응 처리에 실패했습니다.');
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative flex flex-col transition-all duration-1000 ${
        isHighlighted ? 'bg-blue-50/50 ring-2 ring-blue-400/30 rounded-2xl p-4 -mx-4 shadow-sm' : ''
      } ${nested ? 'mt-4 rounded-2xl bg-slate-50/70 px-4 py-4' : 'mt-6 pb-6 border-b border-gray-50 last:border-0'}`}
    >
      {(isCommentAuthor || comment.status !== 'BLINDED') && (
        <div className="absolute right-0 top-0 flex items-center gap-2">
          {isCommentAuthor ? (
            <>
              {comment.status !== 'BLINDED' && (
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(!isEditing);
                    setEditContent(comment.content);
                  }}
                  className="text-[12px] font-medium text-gray-400 hover:text-gray-700"
                >
                  {isEditing ? '취소' : '수정'}
                </button>
              )}
              <button
                type="button"
                onClick={() => handleDeleteComment(comment.commentId)}
                className="text-[12px] font-medium text-red-400 hover:text-red-600"
              >
                삭제
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => onReport('COMMENT', comment.commentId)}
              className="text-[12px] font-medium text-gray-300 hover:text-rose-400 transition-colors"
            >
              신고
            </button>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <UserAvatar
          profileImageUrl={comment.authorProfileImageUrl}
          nickname={comment.authorNickname}
          className="h-[34px] w-[34px] shrink-0 text-[14px]"
        />

        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-center gap-2 pr-14">
            <span className="truncate text-[13.5px] font-bold text-gray-900">
              {comment.authorNickname || '알 수 없음'}
            </span>
            <span className="text-[12px] font-medium tracking-tight text-gray-400">
              {formatDate(comment.createdAt)}
            </span>
          </div>

          {isEditing ? (
            <form onSubmit={handleEditSubmit} className="mt-2 flex flex-col gap-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full min-h-[80px] resize-none rounded-xl border border-gray-200 p-3 text-[14px] outline-none focus:border-blue-500"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="rounded-lg px-3 py-1.5 text-[12px] font-bold text-gray-500 hover:bg-gray-100"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={!editContent.trim() || submittingEdit}
                  className="rounded-lg bg-blue-600 px-3 py-1.5 text-[12px] font-bold text-white disabled:bg-gray-300"
                >
                  저장
                </button>
              </div>
            </form>
          ) : (
            <div
              role={comment.status !== 'BLINDED' ? 'button' : undefined}
              tabIndex={comment.status !== 'BLINDED' ? 0 : undefined}
              onClick={
                comment.status !== 'BLINDED'
                  ? () => {
                      setIsReplying((prev) => {
                        const next = !prev;
                        if (next) {
                          onActivateComment?.();
                        } else {
                          onDeactivateComment?.();
                        }
                        return next;
                      });
                    }
                  : undefined
              }
              onKeyDown={
                comment.status !== 'BLINDED'
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setIsReplying((prev) => {
                          const next = !prev;
                          if (next) {
                            onActivateComment?.();
                          } else {
                            onDeactivateComment?.();
                          }
                          return next;
                        });
                      }
                    }
                  : undefined
              }
              className={comment.status !== 'BLINDED' ? 'cursor-pointer rounded-xl' : undefined}
            >
              {replyToNickname && 'replyToCommentId' in comment && comment.replyToCommentId ? (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onNavigateToComment(comment.replyToCommentId!);
                  }}
                  className="mt-1.5 text-[12px] font-semibold text-blue-500 transition-colors hover:text-blue-700"
                >
                  @{replyToNickname}님에게 답글
                </button>
              ) : null}

              <LinkifiedText
                text={comment.status === 'BLINDED' ? '신고 처리된 댓글입니다.' : comment.content}
                className={`mt-1.5 whitespace-pre-wrap text-[14px] leading-relaxed ${
                  comment.status === 'BLINDED' ? 'italic text-gray-400' : 'text-gray-800'
                }`}
              />
            </div>
          )}

          <div className="mt-2.5 flex items-center gap-3">
            <button
              type="button"
              onClick={handleToggleCommentReaction}
              disabled={comment.status === 'BLINDED'}
              className={`group flex items-center gap-1.5 transition-colors ${
                comment.status === 'BLINDED' ? 'cursor-not-allowed opacity-50' : ''
              }`}
            >
              {isLiked ? (
                <svg className="h-4 w-4 text-rose-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001z" />
                </svg>
              ) : (
                <svg
                  className={`h-4 w-4 ${
                    comment.status === 'BLINDED'
                      ? 'text-gray-200'
                      : 'text-gray-300 group-hover:text-rose-400'
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                  />
                </svg>
              )}
              <span
                className={`text-[12px] font-bold transition-colors ${
                  comment.status === 'BLINDED'
                    ? 'text-gray-300'
                    : isLiked
                      ? 'text-rose-600'
                      : 'text-gray-400 group-hover:text-gray-600'
                }`}
              >
                {comment.likeCount || 0}
              </span>
            </button>
          </div>

          {isReplying && (
            <form onSubmit={handleReplySubmit} className="mt-3 flex flex-col gap-2">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleReplySubmit(e as any);
                  }
                }}
                placeholder={replyPlaceholder}
                className="min-h-[60px] w-full resize-none rounded-xl border border-gray-100 bg-gray-50 p-3 text-[13px] outline-none transition-all focus:border-blue-400 focus:bg-white"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsReplying(false)}
                  className="rounded-lg px-3 py-1.5 text-[12px] font-bold text-gray-500 hover:bg-gray-100"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={!replyContent.trim() || submittingReply}
                  className="rounded-lg bg-blue-600 px-4 py-1.5 text-[12px] font-bold text-white transition-colors disabled:bg-gray-300"
                >
                  {submittingReply ? '등록 중...' : '등록'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

const CommentThreadItem = ({
  thread,
  currentUser,
  handleDeleteComment,
  onNavigateToComment,
  postId,
  refreshComments,
  refreshReplies,
  setPost,
  formatDate,
  onReport,
  highlightedCommentId,
  loadInitialReplies,
  loadMoreReplies,
}: CommentThreadItemProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const threadContainerRef = useRef<HTMLDivElement | null>(null);
  const hasHighlightedReply = thread.replies.some((reply) => reply.commentId === highlightedCommentId);

  useEffect(() => {
    if (hasHighlightedReply) {
      setIsExpanded(true);
    }
  }, [hasHighlightedReply]);

  const handleActivateThread = async () => {
    if (thread.replyCount > 0 && !thread.repliesLoaded) {
      await loadInitialReplies(thread.commentId);
    }

    if (thread.replyCount > 0) {
      setIsExpanded(true);
    }
  };

  const closeThread = () => {
    setIsExpanded(false);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        threadContainerRef.current?.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
          inline: 'nearest',
        });
      });
    });
  };

  const handleReplyMetaToggle = async () => {
    if (isExpanded) {
      closeThread();
      return;
    }

    await handleActivateThread();
  };

  return (
    <div ref={threadContainerRef} style={{ scrollMarginTop: `${COMMENT_SCROLL_OFFSET}px` }}>
      <CommentEntry
        comment={thread}
        currentUser={currentUser}
        handleDeleteComment={handleDeleteComment}
        onNavigateToComment={onNavigateToComment}
        onActivateComment={() => void handleActivateThread()}
        onDeactivateComment={closeThread}
        postId={postId}
        refreshComments={refreshComments}
        refreshReplies={refreshReplies}
        rootCommentId={thread.commentId}
        setPost={setPost}
        formatDate={formatDate}
        onReport={onReport}
        highlightedCommentId={highlightedCommentId}
      />
      {thread.replyCount > 0 && !isExpanded && (
        <div className="ml-[46px] mt-2">
          <button
            type="button"
            onClick={() => void handleReplyMetaToggle()}
            className="text-[12px] font-semibold text-blue-500 transition-colors hover:text-blue-700"
          >
            답글 {thread.replyCount}개
          </button>
        </div>
      )}
      {isExpanded && (
        <div className="ml-[46px] mt-3 border-l border-gray-100 pl-4">
          {thread.repliesLoading && thread.replies.length === 0 ? (
            <div className="py-4 text-[13px] font-medium text-gray-400">답글을 불러오는 중입니다.</div>
          ) : null}
          {thread.replies.map((reply) => (
            <CommentEntry
              key={reply.commentId}
              comment={reply}
              currentUser={currentUser}
              handleDeleteComment={handleDeleteComment}
              onNavigateToComment={onNavigateToComment}
              postId={postId}
              refreshComments={refreshComments}
              refreshReplies={refreshReplies}
              rootCommentId={thread.commentId}
              setPost={setPost}
              formatDate={formatDate}
              onReport={onReport}
              highlightedCommentId={highlightedCommentId}
              nested
            />
          ))}
          {!thread.repliesLoading && thread.repliesLoaded && thread.replies.length === 0 && (
            <div className="py-4 text-[13px] font-medium text-gray-400">표시할 답글이 없습니다.</div>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {thread.repliesHasNext && (
              <button
                type="button"
                onClick={() => void loadMoreReplies(thread.commentId)}
                disabled={thread.repliesLoading}
                className="rounded-full bg-white px-3 py-1 text-[12px] font-bold text-blue-600 ring-1 ring-blue-100 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:text-gray-300"
              >
                {thread.repliesLoading ? '답글을 더 불러오는 중입니다.' : '답글 더 보기'}
              </button>
            )}
            <button
              type="button"
              onClick={closeThread}
              className="rounded-full bg-white px-3 py-1 text-[12px] font-bold text-blue-600 ring-1 ring-blue-100 transition-colors hover:bg-blue-50"
            >
              답글 숨기기
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const PollVotePanel = ({
  detail,
  selectedVote,
  isSubmittingVote,
  onVote,
}: PollVotePanelProps) => {
  const totalVotes = detail.totalVoteCount || 0;
  const optionARate = totalVotes > 0 ? Math.round((detail.optionACount / totalVotes) * 100) : 0;
  const optionBRate = totalVotes > 0 ? Math.round((detail.optionBCount / totalVotes) * 100) : 0;

  return (
    <div className="mt-6 rounded-[28px] border border-gray-200 bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-bold text-emerald-700">
            POLL
          </span>
          <h2 className="mt-3 text-[24px] font-black leading-tight text-gray-900">
            {detail.question}
          </h2>
          <p className="mt-2 text-[13px] font-medium text-gray-500">
            마감 {detail.deadlineAt ? new Date(detail.deadlineAt).toLocaleString('ko-KR') : '-'}
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1.5 text-[12px] font-bold ${
            detail.isClosed ? 'border-rose-100 bg-rose-50 text-rose-700' : 'border-blue-100 bg-blue-50 text-blue-700'
          }`}
        >
          {getStatusLabelWithEmoji(detail.isClosed ? 'CLOSED' : 'OPEN')}
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {[
          {
            voteOption: 'OPTION_A' as const,
            label: detail.optionA,
            count: detail.optionACount,
            rate: optionARate,
            tone: 'bg-emerald-500',
            selectedClass: 'border-emerald-300 bg-emerald-50',
          },
          {
            voteOption: 'OPTION_B' as const,
            label: detail.optionB,
            count: detail.optionBCount,
            rate: optionBRate,
            tone: 'bg-teal-500',
            selectedClass: 'border-teal-300 bg-teal-50',
          },
        ].map((option) => {
          const isSelected = selectedVote === option.voteOption;

          return (
            <button
              key={option.voteOption}
              type="button"
              disabled={detail.isClosed || isSubmittingVote}
              onClick={() => onVote(option.voteOption)}
              className={`rounded-2xl border px-5 py-5 text-left transition ${
                detail.isClosed
                  ? 'cursor-not-allowed border-gray-200 bg-gray-50'
                  : isSelected
                    ? option.selectedClass
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-[16px] font-bold text-gray-900">{option.label}</p>
                <span className="text-[13px] font-bold text-gray-500">{option.count}표</span>
              </div>
              <div className="mt-4 h-2 rounded-full bg-white/90">
                <div className={`h-2 rounded-full ${option.tone}`} style={{ width: `${option.rate}%` }} />
              </div>
              <div className="mt-2 flex items-center justify-between text-[12px] font-medium text-gray-500">
                <span>{option.rate}%</span>
                <span>{isSelected ? '선택됨' : '선택하기'}</span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex items-center justify-between text-[13px] font-medium text-gray-500">
        <span>총 {totalVotes}명 참여</span>
        <span>{detail.isClosed ? '마감된 투표입니다.' : '마감 전까지 선택을 변경할 수 있습니다.'}</span>
      </div>
    </div>
  );
};

const HotdealInfoPanel = ({ detail }: HotdealInfoPanelProps) => {
  const discountRate =
    detail.originalPriceAmount && detail.originalPriceAmount > 0
      ? Math.max(
          0,
          Math.round(
            ((detail.originalPriceAmount - detail.dealPriceAmount) / detail.originalPriceAmount) * 100
          )
        )
      : null;
  const isExpired = detail.expiredAt ? new Date(detail.expiredAt).getTime() <= Date.now() : false;

  return (
    <div className="mt-6 rounded-[28px] border border-gray-200 bg-white p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="inline-flex rounded-full bg-rose-100 px-3 py-1 text-[11px] font-bold text-rose-700">
            HOTDEAL
          </span>
          <h2 className="mt-3 text-[24px] font-black leading-tight text-gray-900">
            {detail.productName}
          </h2>
          <p className="mt-2 text-[13px] font-medium text-gray-500">
            {detail.storeName || '판매처 미정'}
          </p>
        </div>
        <span
          className={`rounded-full border px-3 py-1.5 text-[12px] font-bold ${
            isExpired ? 'border-rose-100 bg-rose-50 text-rose-700' : 'border-blue-100 bg-blue-50 text-blue-700'
          }`}
        >
          {getStatusLabelWithEmoji(isExpired ? 'CLOSED' : 'OPEN')}
        </span>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
          <p className="text-[12px] font-semibold text-gray-400">구매 정보</p>
          <div className="mt-4 space-y-3">
            <div>
              <p className="text-[11px] font-semibold text-gray-400">딜 가격</p>
              <p className="mt-1 text-[28px] font-black leading-none text-gray-900">
                {new Intl.NumberFormat('ko-KR', {
                  style: 'currency',
                  currency: 'KRW',
                  maximumFractionDigits: 0,
                }).format(detail.dealPriceAmount)}
              </p>
            </div>
            {detail.originalPriceAmount ? (
              <div className="flex flex-wrap items-center gap-2 text-[13px] font-semibold">
                <span className="text-gray-400 line-through">
                  {new Intl.NumberFormat('ko-KR', {
                    style: 'currency',
                    currency: 'KRW',
                    maximumFractionDigits: 0,
                  }).format(detail.originalPriceAmount)}
                </span>
                {discountRate != null ? <span className="text-rose-600">{discountRate}% 할인</span> : null}
              </div>
            ) : null}
            {detail.shippingInfo ? (
              <div className="rounded-xl bg-white px-4 py-3 text-[13px] font-medium text-gray-600">
                배송: {detail.shippingInfo}
              </div>
            ) : null}
          </div>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-5">
          <p className="text-[12px] font-semibold text-gray-400">구매 링크</p>
          <div className="mt-4 space-y-3 text-[13px] font-medium text-gray-600">
            <p>종료 {detail.expiredAt ? new Date(detail.expiredAt).toLocaleString('ko-KR') : '-'}</p>
            {detail.dealUrl ? (
              <a
                href={detail.dealUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-slate-900 px-4 text-[14px] font-bold text-white transition hover:bg-slate-800"
              >
                구매처에서 보기
              </a>
            ) : (
              <div className="rounded-xl border border-dashed border-gray-200 px-4 py-3 text-center text-[13px] text-gray-400">
                등록된 링크가 없습니다.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export const PostDetailPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialHighlightedCommentId = searchParams.get('commentId')
    ? Number(searchParams.get('commentId'))
    : null;
  const navigate = useNavigate();

  const [post, setPost] = useState<GetPostResponseDto | null>(null);
  const [comments, setComments] = useState<CommentThreadView[]>([]);
  const [commentPage, setCommentPage] = useState(0);
  const [hasMoreComments, setHasMoreComments] = useState(false);
  const [loadingMoreComments, setLoadingMoreComments] = useState(false);

  const [commentInput, setCommentInput] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pollDetail, setPollDetail] = useState<PollDetailResponseDto | null>(null);
  const [hotdealDetail, setHotdealDetail] = useState<HotdealDetailResponseDto | null>(null);
  const [selectedPollVote, setSelectedPollVote] = useState<'OPTION_A' | 'OPTION_B' | null>(null);
  const [submittingPollVote, setSubmittingPollVote] = useState(false);
  const [isPostMenuOpen, setIsPostMenuOpen] = useState(false);
  const { addToast } = useUIStore();
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);

  const [isDeletePostModalOpen, setIsDeletePostModalOpen] = useState(false);
  const [commentIdToDelete, setCommentIdToDelete] = useState<number | null>(null);

  const reactionStorageKey = `post_reaction_${postId}`;
  const pollVoteStorageKey = `poll_vote_${postId}`;
  const [selectedReaction, setSelectedReaction] = useState<ReactionType | null>(() => {
    const saved = localStorage.getItem(reactionStorageKey);
    return saved === 'LIKE' || saved === 'DISLIKE' ? (saved as ReactionType) : null;
  });

  const [reportModalState, setReportModalState] = useState<{
    isOpen: boolean;
    targetType: ReportTargetType;
    targetId: number;
  }>({
    isOpen: false,
    targetType: 'POST',
    targetId: 0,
  });
  const [highlightedCommentId, setHighlightedCommentId] = useState<number | null>(
    initialHighlightedCommentId
  );

  useEffect(() => {
    setHighlightedCommentId(initialHighlightedCommentId);
  }, [initialHighlightedCommentId]);

  const onReport = (type: ReportTargetType, id: number) => {
    setReportModalState({
      isOpen: true,
      targetType: type,
      targetId: id,
    });
  };

  const handleNavigateToComment = (commentId: number) => {
    setHighlightedCommentId(null);
    window.setTimeout(() => setHighlightedCommentId(commentId), 0);

    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('commentId', String(commentId));
    setSearchParams(nextParams, { replace: true });
  };

  const currentUser = useAuthStore((state) => state.user);

  const isAuthor = useMemo(() => {
    if (!post) return false;
    if (post.isMine) return true;
    return String(currentUser?.userId) === String(post.authorId);
  }, [post, currentUser]);

  const toThreadView = (
    thread: CommentThreadDto,
    previous?: CommentThreadView
  ): CommentThreadView => ({
    ...thread,
    replies: previous?.replies ?? [],
    repliesLoaded: previous?.repliesLoaded ?? false,
    repliesLoading: false,
    repliesPage: previous?.repliesPage ?? -1,
    repliesHasNext: previous?.repliesHasNext ?? thread.replyCount > 0,
  });

  const fetchCommentPages = async (pageCount: number, fetchAll: boolean = false) => {
    if (!postId) {
      return;
    }

    const mergedComments: CommentThreadDto[] = [];
    let pageIndex = 0;
    let hasNextPage = false;

    while (true) {
      const response = await getComments(Number(postId), pageIndex, COMMENT_PAGE_SIZE);
      const nextComments = response.data?.content || [];

      mergedComments.push(...nextComments);
      hasNextPage = response.data?.hasNext || false;

      if (!hasNextPage || (!fetchAll && pageIndex >= pageCount)) {
        setComments((prev) => {
          const previousById = new Map(prev.map((thread) => [thread.commentId, thread]));
          return mergedComments.map((thread) => toThreadView(thread, previousById.get(thread.commentId)));
        });
        setHasMoreComments(hasNextPage);
        setCommentPage(pageIndex);
        return;
      }

      pageIndex += 1;
    }
  };

  const fetchReplyPages = async (rootCommentId: number, pageCount: number) => {
    if (!postId) {
      return;
    }

    setComments((prev) =>
      prev.map((thread) =>
        thread.commentId === rootCommentId ? { ...thread, repliesLoading: true } : thread
      )
    );

    const mergedReplies: CommentReplyDto[] = [];
    let pageIndex = 0;
    let hasNextPage = false;

    try {
      while (true) {
        const response = await getCommentReplies(
          Number(postId),
          rootCommentId,
          pageIndex,
          REPLY_PAGE_SIZE
        );
        const nextReplies = response.data?.content || [];

        mergedReplies.push(...nextReplies);
        hasNextPage = response.data?.hasNext || false;

        if (!hasNextPage || pageIndex >= pageCount) {
          setComments((prev) =>
            prev.map((thread) =>
              thread.commentId === rootCommentId
                ? {
                    ...thread,
                    replies: mergedReplies,
                    repliesLoaded: true,
                    repliesLoading: false,
                    repliesPage: pageIndex,
                    repliesHasNext: hasNextPage,
                  }
                : thread
            )
          );
          return;
        }

        pageIndex += 1;
      }
    } catch {
      setComments((prev) =>
        prev.map((thread) =>
          thread.commentId === rootCommentId ? { ...thread, repliesLoading: false } : thread
        )
      );
    }
  };

  const refreshReplies = async (rootCommentId: number) => {
    const targetThread = comments.find((thread) => thread.commentId === rootCommentId);
    if (!targetThread?.repliesLoaded) {
      return;
    }

    await fetchReplyPages(rootCommentId, Math.max(targetThread.repliesPage, 0));
  };

  useEffect(() => {
    const fetchPostDetail = async () => {
      if (!postId) return;
      setLoading(true);
      setError(null);
      try {
        const postRes = await getPost(Number(postId));
        if (postRes.data) {
          setPost(postRes.data);
          await fetchCommentPages(0);
          const saved = localStorage.getItem(reactionStorageKey);
          setSelectedReaction(
            saved === 'LIKE' || saved === 'DISLIKE' ? (saved as ReactionType) : null
          );
          if (postRes.data.category === 'POLL') {
            const pollRes = await getPollDetail(Number(postId));
            setPollDetail(pollRes.data ?? null);
            const savedPollVote = localStorage.getItem(pollVoteStorageKey);
            setSelectedPollVote(
              savedPollVote === 'OPTION_A' || savedPollVote === 'OPTION_B'
                ? (savedPollVote as 'OPTION_A' | 'OPTION_B')
                : null
            );
            setHotdealDetail(null);
          } else if (postRes.data.category === 'HOTDEAL') {
            const hotdealRes = await getHotdealDetail(Number(postId));
            setHotdealDetail(hotdealRes.data ?? null);
            setPollDetail(null);
            setSelectedPollVote(null);
          } else {
            setPollDetail(null);
            setHotdealDetail(null);
            setSelectedPollVote(null);
          }
        } else {
          setError('게시글을 찾을 수 없습니다.');
        }
      } catch {
        setError('게시글을 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };
    fetchPostDetail();
  }, [pollVoteStorageKey, postId, reactionStorageKey]);

  const refreshComments = async (fetchAll: boolean = false) => {
    if (!postId) return;
    const loadedReplyTargets = comments
      .filter((thread) => thread.repliesLoaded)
      .map((thread) => ({ rootCommentId: thread.commentId, replyPage: Math.max(thread.repliesPage, 0) }));

    await fetchCommentPages(commentPage, fetchAll);

    for (const target of loadedReplyTargets) {
      await fetchReplyPages(target.rootCommentId, target.replyPage);
    }
  };

  const handleDelete = async () => {
    setIsDeletePostModalOpen(true);
  };

  const handleConfirmDeletePost = async () => {
    if (!postId) return;
    try {
      await deletePost(Number(postId));
      addToast('게시글이 삭제되었습니다.', 'success');
      navigate('/community');
    } catch {
      addToast('게시글 삭제에 실패했습니다.', 'error');
    } finally {
      setIsDeletePostModalOpen(false);
    }
  };

  const handleDeleteComment = (commentId: number) => {
    setCommentIdToDelete(commentId);
  };

  const handleConfirmDeleteComment = async () => {
    if (!commentIdToDelete) return;
    try {
      await deleteComment(commentIdToDelete);
      await refreshComments(true);
      setPost((prev) =>
        prev ? { ...prev, commentCount: Math.max(0, prev.commentCount - 1) } : null
      );
      addToast('댓글이 삭제되었습니다.', 'success');
    } catch {
      addToast('댓글 삭제에 실패했습니다.', 'error');
    } finally {
      setCommentIdToDelete(null);
    }
  };

  const handleCommentSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const finalContent = commentInput.trim().replace(/\n{3,}/g, '\n\n');
    if (!postId || !finalContent || submittingComment) return;
    setSubmittingComment(true);
    try {
      await createComment(Number(postId), { content: finalContent });
      setCommentInput('');
      await refreshComments(true);
      setPost((prev) => (prev ? { ...prev, commentCount: prev.commentCount + 1 } : null));
    } catch {
      alert('댓글 작성에 실패했습니다.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const loadMoreComments = async () => {
    if (!postId || !hasMoreComments || loadingMoreComments) return;
    setLoadingMoreComments(true);
    try {
      const nextPage = commentPage + 1;
      const res = await getComments(Number(postId), nextPage, COMMENT_PAGE_SIZE);
      if (res.data) {
        setComments((prev) => {
          const previousById = new Map(prev.map((thread) => [thread.commentId, thread]));
          const nextThreads = (res.data?.content || []).map((thread) =>
            toThreadView(thread, previousById.get(thread.commentId))
          );
          return [...prev, ...nextThreads];
        });
        setHasMoreComments(res.data.hasNext);
        setCommentPage(nextPage);
      }
    } catch {

    } finally {
      setLoadingMoreComments(false);
    }
  };

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!hasMoreComments) {
      return;
    }

    const maybeLoadMore = (remainingScroll: number) => {
      if (remainingScroll <= 240) {
        void loadMoreComments();
      }
    };

    const handleContainerScroll = () => {
      if (!container) {
        return;
      }
      maybeLoadMore(container.scrollHeight - container.scrollTop - container.clientHeight);
    };

    const handleWindowScroll = () => {
      const scrollRoot = document.documentElement;
      maybeLoadMore(scrollRoot.scrollHeight - window.scrollY - window.innerHeight);
    };

    container?.addEventListener('scroll', handleContainerScroll, { passive: true });
    window.addEventListener('scroll', handleWindowScroll, { passive: true });

    handleContainerScroll();
    handleWindowScroll();

    return () => {
      container?.removeEventListener('scroll', handleContainerScroll);
      window.removeEventListener('scroll', handleWindowScroll);
    };
  }, [hasMoreComments, loadingMoreComments, commentPage, postId]);

  const loadInitialReplies = async (rootCommentId: number) => {
    await fetchReplyPages(rootCommentId, 0);
  };

  const loadMoreReplies = async (rootCommentId: number) => {
    const targetThread = comments.find((thread) => thread.commentId === rootCommentId);
    if (!targetThread || targetThread.repliesLoading || !targetThread.repliesHasNext) {
      return;
    }

    await fetchReplyPages(rootCommentId, targetThread.repliesPage + 1);
  };

  const handlePollVote = async (voteOption: 'OPTION_A' | 'OPTION_B') => {
    if (!postId || !pollDetail || pollDetail.isClosed || submittingPollVote) return;

    setSubmittingPollVote(true);
    try {
      const res = await submitPollVote(Number(postId), { voteOption });
      if (res.data) {
        setPollDetail((prev) =>
          prev
            ? {
                ...prev,
                optionACount: res.data.optionACount,
                optionBCount: res.data.optionBCount,
                totalVoteCount: res.data.totalVoteCount,
              }
            : prev
        );
        setSelectedPollVote(voteOption);
        localStorage.setItem(pollVoteStorageKey, voteOption);
      }
    } catch {
      alert('투표에 실패했습니다.');
    } finally {
      setSubmittingPollVote(false);
    }
  };

  const handleToggleReaction = async (rType: ReactionType) => {
    if (!postId || !post || post.status === 'BLINDED') return;
    const oppositeType: ReactionType = rType === 'LIKE' ? 'DISLIKE' : 'LIKE';
    const isCurrentActive = selectedReaction === rType;
    const isOppositeActive = selectedReaction === oppositeType;

    try {
      if (!isCurrentActive && isOppositeActive) {
        const resOpp = await toggleReaction({
          targetType: 'POST',
          targetId: Number(postId),
          reactionType: oppositeType,
          active: false,
        });
        if (resOpp.data) {
          setPost((prev) =>
            prev
              ? {
                  ...prev,
                  likeCount: resOpp.data!.likeCount,
                  dislikeCount: resOpp.data!.dislikeCount,
                }
              : null
          );
          setSelectedReaction(null);
        }
      }

      const nextActive = !isCurrentActive;
      const res = await toggleReaction({
        targetType: 'POST',
        targetId: Number(postId),
        reactionType: rType,
        active: nextActive,
      });
      if (res.data) {
        setPost((prev) =>
          prev
            ? { ...prev, likeCount: res.data!.likeCount, dislikeCount: res.data!.dislikeCount }
            : null
        );
        const nextState = res.data!.active ? res.data!.reactionType : null;
        setSelectedReaction(nextState);
        if (nextState) localStorage.setItem(reactionStorageKey, nextState);
        else localStorage.removeItem(reactionStorageKey);
      }
    } catch (error: unknown) {
      const axiosError = error as { response?: { status: number } };
      if (axiosError.response?.status === 409) {
        setSelectedReaction(rType);
        localStorage.setItem(reactionStorageKey, rType);
        const postRes = await getPost(Number(postId));
        if (postRes.data) setPost(postRes.data);
      } else {
        alert('반응 처리에 실패했습니다.');
      }
    }
  };

  const getCategoryName = (cat: BoardCategory | undefined) => {
    switch (cat) {
      case 'FREE':
        return '자유';
      case 'COHORT':
        return '기수';
      case 'PR':
        return 'PR';
      case 'POLL':
        return '투표';
      case 'HOTDEAL':
        return '핫딜';
      default:
        return '전체';
    }
  };

  const getCategoryDot = (cat: BoardCategory | undefined) => {
    switch (cat) {
      case 'FREE':
        return 'bg-blue-400';
      case 'COHORT':
        return 'bg-violet-400';
      case 'PR':
        return 'bg-amber-400';
      case 'POLL':
        return 'bg-emerald-400';
      case 'HOTDEAL':
        return 'bg-rose-400';
      default:
        return 'bg-gray-300';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Card className="!p-0 min-h-[600px] overflow-hidden flex items-center justify-center p-12">
        <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary-blue border-t-transparent" />
      </Card>
    );
  }

  if (error || !post) {
    return (
      <Card className="!p-0 min-h-[600px] overflow-hidden flex flex-col items-center justify-center p-12">
        <p className="mb-2 text-[18px] font-bold text-gray-700">
          {error || '게시글을 찾을 수 없습니다.'}
        </p>
        <Button onClick={() => navigate('/community')} className="mt-4 !px-6 !py-2.5">
          목록으로 돌아가기
        </Button>
      </Card>
    );
  }

  return (
    <Card className="!p-0 flex min-h-[600px] flex-col overflow-hidden">
      <div className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-gray-100 bg-white/80 px-4 backdrop-blur-md">
        <button
          onClick={() => navigate('/community')}
          className="-ml-2 p-2 text-gray-800 transition-colors hover:text-black"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="text-[16px] font-bold tracking-[-0.01em] text-gray-900">
          {getCategoryName(post.category)}
        </span>
        <div className="flex w-10 justify-end">
          {isAuthor ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsPostMenuOpen(!isPostMenuOpen)}
                className={`-mr-2 p-2 transition-colors ${
                  isPostMenuOpen ? 'text-gray-900 bg-gray-50 rounded-full' : 'text-gray-400 hover:text-gray-700'
                }`}
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                  />
                </svg>
              </button>

              {isPostMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setIsPostMenuOpen(false)}
                  />
                  <div className="absolute right-0 top-full z-20 mt-1 flex w-28 flex-col overflow-hidden rounded-xl border border-gray-100 bg-white shadow-lg animate-in fade-in slide-in-from-top-1">
                    <button
                      className="border-b border-gray-50 px-4 py-2.5 text-left text-[14px] font-medium text-gray-700 hover:bg-gray-50"
                      onClick={() => {
                        setIsPostMenuOpen(false);
                        navigate(`/community/${postId}/edit`);
                      }}
                    >
                      수정
                    </button>
                    <button
                      className="px-4 py-2.5 text-left text-[14px] font-medium text-red-500 hover:bg-red-50"
                      onClick={() => {
                        setIsPostMenuOpen(false);
                        handleDelete();
                      }}
                    >
                      삭제
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => onReport('POST', Number(postId))}
              className="-mr-2 p-2 text-gray-400 transition-colors hover:text-rose-500"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2.2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 18v-6a5 5 0 1 1 10 0v6" />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 21a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-1a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M21 12h1M12 2v1m-6.5 1.5L4 3M18.5 4.5 20 3M2 12h1"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div ref={scrollContainerRef} className="w-full overflow-y-auto">
        <div className="flex w-full items-start gap-3 px-5 pt-6">
          <UserAvatar
            profileImageUrl={post.authorProfileImageUrl}
            nickname={post.authorNickname}
            className={`h-[42px] w-[42px] shrink-0 text-[18px] ${getCategoryDot(post.category)} text-white`}
          />
          <div className="pt-0.5">
            <div className="text-[15px] font-bold leading-tight text-gray-900">
              {post.authorNickname || '알 수 없음'}
            </div>
            <div className="mt-1 text-[13px] font-bold text-text-muted">
              {formatDate(post.createdAt)}
            </div>
          </div>
        </div>

        <div className="mt-5 px-5">
          <h1
            className={`whitespace-pre-wrap text-[20px] font-bold leading-snug tracking-[-0.01em] ${
              post.status === 'BLINDED' ? 'italic text-gray-400' : 'text-gray-900'
            }`}
          >
            {post.status === 'BLINDED' ? '신고 처리된 게시물입니다.' : post.title}
          </h1>
          {post.status !== 'BLINDED' && post.category === 'POLL' && pollDetail ? (
            <PollVotePanel
              detail={pollDetail}
              selectedVote={selectedPollVote}
              isSubmittingVote={submittingPollVote}
              onVote={handlePollVote}
            />
          ) : null}
          {post.status !== 'BLINDED' && post.category === 'HOTDEAL' && hotdealDetail ? (
            <HotdealInfoPanel detail={hotdealDetail} />
          ) : null}
          <LinkifiedText
            text={post.status === 'BLINDED' ? '신고 처리된 게시물입니다.' : post.content}
            className={`mt-4 whitespace-pre-wrap text-[16px] font-medium leading-[1.65] word-break-all ${
              post.status === 'BLINDED' ? 'italic text-gray-400' : 'text-gray-800'
            }`}
          />
          {post.status !== 'BLINDED' && post.attachments.length > 0 ? (
            <div className="mt-5 space-y-3 rounded-2xl border border-gray-100 bg-gray-50/70 p-4">
              <div className="text-[13px] font-bold text-gray-700">
                첨부파일 {post.attachments.length}개
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {post.attachments.map((attachment) => {
                  const isImage = attachment.contentType.startsWith('image/');

                  return (
                    <a
                      key={attachment.attachmentId}
                      href={attachment.fileUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="overflow-hidden rounded-2xl border border-gray-200 bg-white transition hover:border-blue-200 hover:shadow-sm"
                    >
                      {isImage ? (
                        <img
                          src={attachment.fileUrl}
                          alt={attachment.fileName}
                          className="h-44 w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-44 items-center justify-center bg-gray-50 text-[13px] font-semibold text-gray-400">
                          파일 미리보기를 지원하지 않습니다.
                        </div>
                      )}
                      <div className="flex items-center justify-between gap-3 px-4 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-[13px] font-semibold text-gray-800">
                            {attachment.fileName}
                          </p>
                          <p className="mt-1 text-[12px] text-gray-400">
                            {Math.max(1, Math.round(attachment.fileSize / 1024))} KB
                          </p>
                        </div>
                        <span className="text-[12px] font-bold text-blue-600">열기</span>
                      </div>
                    </a>
                  );
                })}
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-10 flex items-center gap-2 px-5">
          <button
            onClick={() => handleToggleReaction('LIKE')}
            disabled={post.status === 'BLINDED'}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${
              post.status === 'BLINDED'
                ? 'cursor-not-allowed border-gray-100 opacity-50'
                : selectedReaction === 'LIKE'
                  ? 'border border-blue-500 bg-blue-50'
                  : 'border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <svg
              className={`h-[18px] w-[18px] ${
                post.status === 'BLINDED'
                  ? 'text-gray-300'
                  : selectedReaction === 'LIKE'
                    ? 'text-blue-600'
                    : 'text-gray-800'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="2.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
              />
            </svg>
            <span
              className={`text-[13px] font-medium ${
                post.status === 'BLINDED'
                  ? 'text-gray-400'
                  : selectedReaction === 'LIKE'
                    ? 'text-blue-700'
                    : 'text-gray-700'
              }`}
            >
              좋아요 {post.likeCount}
            </span>
          </button>
          <button
            onClick={() => handleToggleReaction('DISLIKE')}
            disabled={post.status === 'BLINDED'}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${
              post.status === 'BLINDED'
                ? 'cursor-not-allowed border-gray-100 opacity-50'
                : selectedReaction === 'DISLIKE'
                  ? 'border border-blue-500 bg-blue-50'
                  : 'border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <svg
              className={`h-[18px] w-[18px] ${
                post.status === 'BLINDED'
                  ? 'text-gray-300'
                  : selectedReaction === 'DISLIKE'
                    ? 'text-blue-600'
                    : 'text-gray-800'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
              />
            </svg>
            <span
              className={`text-[13px] font-medium ${
                post.status === 'BLINDED'
                  ? 'text-gray-400'
                  : selectedReaction === 'DISLIKE'
                    ? 'text-blue-700'
                    : 'text-gray-700'
              }`}
            >
              싫어요 {post.dislikeCount}
            </span>
          </button>
        </div>

        <div className="mt-6 h-2.5 w-full border-y border-gray-100 bg-gray-50" />

        <div className="w-full px-5 pt-6 pb-24">
          <h3 className="mb-5 text-[15px] font-bold text-gray-900">{post.commentCount}개의 댓글</h3>

          {post.status !== 'BLINDED' && (
            <form
              onSubmit={handleCommentSubmit}
              className="mb-8 flex flex-col gap-3 rounded-[28px] border border-gray-200 bg-gray-50/50 p-5 focus-within:border-blue-400 focus-within:bg-white transition-all shadow-sm"
            >
              <textarea
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleCommentSubmit(e as any);
                  }
                }}
                placeholder="따뜻한 댓글을 남겨주세요."
                className="min-h-[100px] w-full resize-none border-none bg-transparent text-[14.5px] leading-relaxed text-gray-800 outline-none placeholder:text-gray-400"
              />
              <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                <span className="text-[11px] font-medium text-gray-400">
                  Enter로 등록, Shift+Enter로 줄바꿈
                </span>
                <button
                  type="submit"
                  disabled={submittingComment || !commentInput.trim()}
                  className="rounded-full bg-blue-600 px-6 py-2.5 text-[13.5px] font-bold text-white shadow-lg shadow-blue-100 transition-all hover:bg-blue-700 disabled:bg-gray-200 disabled:shadow-none"
                >
                  {submittingComment ? '등록 중...' : '댓글 등록'}
                </button>
              </div>
            </form>
          )}

          <div className="flex flex-col">
            {comments.length === 0 ? (
              <div className="py-10 text-center text-[14px] font-medium text-gray-400">
                첫 번째 댓글을 남겨보세요.
              </div>
            ) : (
              comments.map((thread) => (
                <CommentThreadItem
                  key={thread.commentId}
                  thread={thread}
                  currentUser={currentUser}
                  handleDeleteComment={handleDeleteComment}
                  onNavigateToComment={handleNavigateToComment}
                  postId={postId}
                  refreshComments={refreshComments}
                  refreshReplies={refreshReplies}
                  rootCommentId={thread.commentId}
                  setPost={setPost}
                  formatDate={formatDate}
                  onReport={onReport}
                  highlightedCommentId={highlightedCommentId}
                  loadInitialReplies={loadInitialReplies}
                  loadMoreReplies={loadMoreReplies}
                />
              ))
            )}
          </div>

          {hasMoreComments && (
            <div className="mt-6 flex justify-center py-4">
              {loadingMoreComments ? (
                <div className="flex items-center gap-2 text-[13px] font-medium text-gray-400">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500" />
                  <span>댓글을 더 불러오는 중입니다.</span>
                </div>
              ) : (
                <span className="text-[13px] font-medium text-gray-400">
                  스크롤하면 댓글을 더 불러옵니다.
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      <ReportModal
        isOpen={reportModalState.isOpen}
        onClose={() => setReportModalState((prev) => ({ ...prev, isOpen: false }))}
        targetType={reportModalState.targetType}
        targetId={reportModalState.targetId}
      />

      {}
      <Modal
        isOpen={isDeletePostModalOpen}
        onClose={() => setIsDeletePostModalOpen(false)}
        title="게시글 삭제"
        footer={
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setIsDeletePostModalOpen(false)}
              className="!px-6"
            >
              취소
            </Button>
            <Button
              className="!bg-rose-500 !border-rose-500 hover:!bg-rose-600 !px-6"
              onClick={handleConfirmDeletePost}
            >
              삭제하기
            </Button>
          </div>
        }
      >
        <p className="text-[15px] font-medium text-gray-600 leading-relaxed">
          정말 이 게시글을 삭제하시겠습니까? <br />
          삭제된 게시글은 다시 복구할 수 없습니다.
        </p>
      </Modal>

      {}
      <Modal
        isOpen={commentIdToDelete !== null}
        onClose={() => setCommentIdToDelete(null)}
        title="댓글 삭제"
        footer={
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setCommentIdToDelete(null)}
              className="!px-6"
            >
              취소
            </Button>
            <Button
              className="!bg-rose-500 !border-rose-500 hover:!bg-rose-600 !px-6"
              onClick={handleConfirmDeleteComment}
            >
              삭제하기
            </Button>
          </div>
        }
      >
        <p className="text-[15px] font-medium text-gray-600 leading-relaxed">
          정말 이 댓글을 삭제하시겠습니까? <br />
          삭제된 댓글은 다시 복구할 수 없습니다.
        </p>
      </Modal>
    </Card>
  );
};
