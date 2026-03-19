import axios from 'axios';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  createComment,
  deleteComment,
  deletePost,
  getComments,
  getHotdealDetail,
  getPollDetail,
  getPost,
  submitPollVote,
  toggleReaction,
  updateComment,
} from '../api/communityApi';
import type {
  BoardCategory,
  CommentSummaryDto,
  GetPostResponseDto,
  HotdealDetailResponseDto,
  PollDetailResponseDto,
  ReactionType,
} from '../types';
import { useAuthStore } from '@/features/auth/store/useAuthStore';

export const PostDetailPage = () => {
  const { postId } = useParams<{ postId: string }>();
  const navigate = useNavigate();

  const [post, setPost] = useState<GetPostResponseDto | null>(null);
  const [comments, setComments] = useState<CommentSummaryDto[]>([]);
  const [commentPage, setCommentPage] = useState(0);
  const [hasMoreComments, setHasMoreComments] = useState(false);

  const [commentInput, setCommentInput] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [submittingPollVote, setSubmittingPollVote] = useState(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pollDetail, setPollDetail] = useState<PollDetailResponseDto | null>(null);
  const [hotdealDetail, setHotdealDetail] = useState<HotdealDetailResponseDto | null>(null);

  // 추가: 현재 내가 누른 반응 상태 (localStorage로 유지)
  const reactionStorageKey = `post_reaction_${postId}`;
  const [selectedReaction, setSelectedReaction] = useState<ReactionType | null>(() => {
    const saved = localStorage.getItem(`post_reaction_${postId}`);
    return saved === 'LIKE' || saved === 'DISLIKE' ? saved : null;
  });

  const currentUser = useAuthStore((state) => state.user);
  const isAuthor = post?.isMine ?? currentUser?.userId === post?.authorId;

  useEffect(() => {
    const fetchPostDetail = async () => {
      if (!postId) return;

      setLoading(true);
      setError(null);

      try {
        const [postRes, commentsRes] = await Promise.all([
          getPost(Number(postId)),
          getComments(Number(postId), 0, 4),
        ]);

        if (postRes.data) {
          setPost(postRes.data);
          if (postRes.data.category === 'POLL') {
            const pollRes = await getPollDetail(Number(postId));
            setPollDetail(pollRes.data ?? null);
            setHotdealDetail(null);
          } else if (postRes.data.category === 'HOTDEAL') {
            const hotdealRes = await getHotdealDetail(Number(postId));
            setHotdealDetail(hotdealRes.data ?? null);
            setPollDetail(null);
          } else {
            setPollDetail(null);
            setHotdealDetail(null);
          }
          setComments(commentsRes.data?.content || []);
          setHasMoreComments(commentsRes.data?.hasNext || false);
          setCommentPage(0);

          // localStorage에서 복원
          const saved = localStorage.getItem(reactionStorageKey);
          setSelectedReaction(saved === 'LIKE' || saved === 'DISLIKE' ? saved : null);
        } else {
          setError('게시글을 찾을 수 없습니다.');
        }
      } catch (err) {
        console.error('Failed to fetch post detail or comments:', err);
        setError('게시글을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchPostDetail();
  }, [postId]);

  const handlePollVote = async (voteOption: 'OPTION_A' | 'OPTION_B') => {
    if (!postId || !pollDetail || pollDetail.isClosed || submittingPollVote) return;

    setSubmittingPollVote(true);
    try {
      const voteRes = await submitPollVote(Number(postId), { voteOption });
      if (voteRes.data) {
        setPollDetail((prev) =>
          prev
            ? {
                ...prev,
                myVoteOption: voteRes.data.voteOption,
                optionACount: voteRes.data.optionACount,
                optionBCount: voteRes.data.optionBCount,
                totalVoteCount: voteRes.data.totalVoteCount,
                updatedAt: voteRes.data.updatedAt,
              }
            : prev
        );
      } else {
        const refreshed = await getPollDetail(Number(postId));
        setPollDetail(refreshed.data ?? null);
      }
    } catch (voteError) {
      console.error('Failed to submit poll vote:', voteError);
      alert('투표 처리에 실패했습니다.');
    } finally {
      setSubmittingPollVote(false);
    }
  };

  const refreshCommentsFirstPage = async () => {
    if (!postId) return;

    const commentsRes = await getComments(Number(postId), 0, 4);
    setComments(commentsRes.data?.content || []);
    setHasMoreComments(commentsRes.data?.hasNext || false);
    setCommentPage(0);
  };

  const handleDelete = async () => {
    if (!postId || !window.confirm('정말 이 게시글을 삭제하시겠습니까?')) return;

    try {
      await deletePost(Number(postId));
      navigate('/community');
    } catch (err) {
      console.error('Failed to delete post:', err);
      alert('게시글 삭제에 실패했습니다.');
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!window.confirm('정말 이 댓글을 삭제하시겠습니까?')) return;

    try {
      await deleteComment(commentId);
      await refreshCommentsFirstPage();

      setPost((prev) =>
        prev
          ? {
              ...prev,
              commentCount: Math.max(0, prev.commentCount - 1),
            }
          : prev
      );
    } catch (err) {
      console.error('Failed to delete comment:', err);
      alert('댓글 삭제에 실패했습니다.');
    }
  };

  const handleEditComment = async (comment: CommentSummaryDto) => {
    const nextContent = window.prompt('댓글을 수정하세요.', comment.content);

    if (nextContent == null) return;
    if (!nextContent.trim()) {
      alert('댓글 내용을 입력해주세요.');
      return;
    }

    try {
      await updateComment(comment.commentId, { content: nextContent.trim() });
      setComments((prev) =>
        prev.map((item) =>
          item.commentId === comment.commentId
            ? {
                ...item,
                content: nextContent.trim(),
              }
            : item
        )
      );
    } catch (err) {
      console.error('Failed to update comment:', err);
      alert('댓글 수정에 실패했습니다.');
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!postId || !commentInput.trim() || submittingComment) return;

    setSubmittingComment(true);
    try {
      await createComment(Number(postId), { content: commentInput.trim() });
      setCommentInput('');
      await refreshCommentsFirstPage();

      setPost((prev) =>
        prev
          ? {
              ...prev,
              commentCount: prev.commentCount + 1,
            }
          : prev
      );
    } catch (err) {
      console.error('Failed to create comment:', err);
      alert('댓글 작성에 실패했습니다.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const loadMoreComments = async () => {
    if (!postId || !hasMoreComments) return;

    try {
      const nextPage = commentPage + 1;
      const res = await getComments(Number(postId), nextPage, 4);

      if (res.data) {
        setComments((prev) => [...prev, ...(res.data?.content || [])]);
        setHasMoreComments(res.data.hasNext);
        setCommentPage(nextPage);
      }
    } catch (err) {
      console.error('Failed to load more comments:', err);
    }
  };

  const handleToggleReaction = async (rType: ReactionType) => {
    if (!postId || !post) return;

    try {
      const res = await toggleReaction({
        targetType: 'POST',
        targetId: Number(postId),
        reactionType: rType,
        active: true,
      });

      if (res.data) {
        setPost({
          ...post,
          likeCount: res.data.likeCount,
          dislikeCount: res.data.dislikeCount,
        });

        // 반응 등록되면 해당 버튼 활성화 + localStorage 저장
        const nextReaction = res.data.active ? res.data.reactionType : null;
        setSelectedReaction(nextReaction);
        if (nextReaction) {
          localStorage.setItem(reactionStorageKey, nextReaction);
        } else {
          localStorage.removeItem(reactionStorageKey);
        }
      }
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        try {
          const cancelRes = await toggleReaction({
            targetType: 'POST',
            targetId: Number(postId),
            reactionType: rType,
            active: false,
          });

          if (cancelRes.data) {
            setPost({
              ...post,
              likeCount: cancelRes.data.likeCount,
              dislikeCount: cancelRes.data.dislikeCount,
            });

            // 반응 취소되면 비활성화 + localStorage 업데이트
            const nextReaction = cancelRes.data.active ? cancelRes.data.reactionType : null;
            setSelectedReaction(nextReaction);
            if (nextReaction) {
              localStorage.setItem(reactionStorageKey, nextReaction);
            } else {
              localStorage.removeItem(reactionStorageKey);
            }
          }
        } catch (cancelErr) {
          console.error('Failed to cancel reaction:', cancelErr);
          alert('반응 취소에 실패했습니다.');
        }
      } else {
        console.error('Failed to toggle reaction:', error);
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
        return '토론';
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

  const toPercent = (value: number) => `${Math.round(value)}%`;
  const toWon = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const pollSummary = pollDetail ?? post?.extraSummary?.poll;
  const pollOptionACount = pollSummary?.optionACount ?? 0;
  const pollOptionBCount = pollSummary?.optionBCount ?? 0;
  const pollTotal = Math.max(1, pollOptionACount + pollOptionBCount);
  const pollOptionARate = (pollOptionACount / pollTotal) * 100;
  const pollOptionBRate = (pollOptionBCount / pollTotal) * 100;
  const myVoteOption =
    pollDetail && 'myVoteOption' in pollDetail ? pollDetail.myVoteOption ?? null : null;
  const votedA = myVoteOption === 'OPTION_A';
  const votedB = myVoteOption === 'OPTION_B';
  const hotdealSummary = hotdealDetail ?? post?.extraSummary?.hotdeal;
  const hotdealIsExpired = hotdealSummary
    ? 'isExpired' in hotdealSummary
      ? hotdealSummary.isExpired
      : Boolean(hotdealSummary.expiredAt) &&
        new Date(hotdealSummary.expiredAt).getTime() <= Date.now()
    : false;
  const hotdealDiscountRate =
    hotdealSummary?.originalPriceAmount && hotdealSummary.originalPriceAmount > 0
      ? Math.max(
          0,
          Math.round(
            ((hotdealSummary.originalPriceAmount - (hotdealSummary.dealPriceAmount ?? 0)) /
              hotdealSummary.originalPriceAmount) *
              100
          )
        )
      : 0;

  const isCommentAuthor = (comment: CommentSummaryDto) =>
    comment.isMine ?? currentUser?.userId === comment.authorId;

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px] items-center justify-center p-12">
        <div className="w-8 h-8 border-4 border-gray-100 border-t-blue-500 rounded-full animate-spin mb-4" />
        <p className="text-gray-400 font-medium text-[14px]">게시글을 불러오는 중...</p>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col min-h-[600px] items-center justify-center p-12">
        <div className="w-16 h-16 rounded-xl bg-red-50 flex items-center justify-center mb-4">
          <svg
            className="w-8 h-8 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-gray-700 font-bold text-[18px] mb-2">
          {error || '게시글을 찾을 수 없습니다.'}
        </p>
        <button
          onClick={() => navigate('/community')}
          className="mt-4 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-colors shadow-sm text-[14px]"
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100/80 overflow-hidden flex flex-col">
      <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md px-4 h-14 flex items-center justify-between border-b border-gray-100">
        <button
          onClick={() => navigate('/community')}
          className="p-2 -ml-2 text-gray-800 hover:text-black transition-colors"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <span className="font-bold text-[16px] text-gray-900 tracking-[-0.01em]">
          {getCategoryName(post.category)}
        </span>

        <div className="w-10 flex justify-end">
          {isAuthor ? (
            <div className="relative group">
              <button className="p-2 -mr-2 text-gray-400 hover:text-gray-700">
                <svg
                  className="w-5 h-5"
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

              <div className="absolute right-0 top-full mt-1 w-28 bg-white border border-gray-100 rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all flex flex-col overflow-hidden">
                <button
                  className="px-4 py-2.5 text-left text-[14px] font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-50"
                  onClick={() => navigate(`/community/${postId}/edit`)}
                >
                  수정
                </button>
                <button
                  className="px-4 py-2.5 text-left text-[14px] font-medium text-red-500 hover:bg-red-50"
                  onClick={handleDelete}
                >
                  삭제
                </button>
              </div>
            </div>
          ) : (
            <button className="p-2 -mr-2 text-gray-800 hover:text-black">
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      <div className="w-full overflow-y-auto">
        <div className="px-5 pt-6 flex items-start gap-3 w-full">
          <div
            className={`w-[42px] h-[42px] rounded-full flex items-center justify-center text-white font-bold text-[18px] shrink-0 ${getCategoryDot(post.category)}`}
          >
            {(post.authorNickname || '?')[0]}
          </div>

          <div className="pt-0.5">
            <div className="text-[15px] font-bold text-gray-900 leading-tight">
              {post.authorNickname || '알 수 없음'}
            </div>
            <div className="text-[12px] text-gray-400 font-medium mt-0.5">
              {formatDate(post.createdAt).split('.').slice(1, 3).join('.')}
            </div>
          </div>
        </div>

        <div className="px-5 mt-5">
          <h1 className="text-[20px] font-bold text-gray-900 leading-snug tracking-[-0.01em] whitespace-pre-wrap">
            {post.title}
          </h1>
          <div className="mt-4 text-[16px] text-gray-800 leading-[1.65] font-medium whitespace-pre-wrap word-break-all">
            {post.content}
          </div>

          {post.category === 'POLL' && (
            <section className="mt-5 rounded-2xl border border-emerald-100 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${
                    pollSummary?.isClosed
                      ? 'bg-slate-200 text-slate-600'
                      : 'bg-emerald-100 text-emerald-700'
                  }`}
                >
                  {pollSummary?.isClosed ? '투표 종료' : '투표 진행 중'}
                </span>
                <span className="text-[12px] font-semibold text-slate-500">
                  총 {pollSummary?.totalVoteCount ?? pollOptionACount + pollOptionBCount}표
                </span>
              </div>

              <p className="text-[15px] font-bold text-slate-900 leading-snug">
                {pollSummary?.question ?? '토론 질문이 등록된 게시글입니다.'}
              </p>

              <div className="mt-4 space-y-3">
                <button
                  type="button"
                  disabled={Boolean(pollSummary?.isClosed) || submittingPollVote}
                  onClick={() => handlePollVote('OPTION_A')}
                  className={`w-full rounded-xl border px-3 py-2.5 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${
                    votedA
                      ? 'border-emerald-500 bg-emerald-50'
                      : 'border-emerald-100 bg-white hover:bg-emerald-50/40'
                  }`}
                >
                  <div className="mb-1.5 flex items-center justify-between text-[12px] font-semibold text-slate-700">
                    <span>{pollSummary?.optionA ?? '선택지 A'}</span>
                    <span>{toPercent(pollOptionARate)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-emerald-500 transition-all"
                      style={{ width: `${pollOptionARate}%` }}
                    />
                  </div>
                </button>

                <button
                  type="button"
                  disabled={Boolean(pollSummary?.isClosed) || submittingPollVote}
                  onClick={() => handlePollVote('OPTION_B')}
                  className={`w-full rounded-xl border px-3 py-2.5 text-left transition disabled:cursor-not-allowed disabled:opacity-60 ${
                    votedB
                      ? 'border-cyan-500 bg-cyan-50'
                      : 'border-cyan-100 bg-white hover:bg-cyan-50/40'
                  }`}
                >
                  <div className="mb-1.5 flex items-center justify-between text-[12px] font-semibold text-slate-700">
                    <span>{pollSummary?.optionB ?? '선택지 B'}</span>
                    <span>{toPercent(pollOptionBRate)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-cyan-500 transition-all"
                      style={{ width: `${pollOptionBRate}%` }}
                    />
                  </div>
                </button>
              </div>

              <div className="mt-3 text-[11px] font-medium text-slate-500">
                마감: {pollSummary?.deadlineAt ? formatDate(pollSummary.deadlineAt) : '-'}
              </div>

            </section>
          )}

          {post.category === 'HOTDEAL' && (
            <section className="mt-5 rounded-2xl border border-rose-100 bg-white p-4 shadow-sm">
              <div className="mb-3 flex items-center justify-between">
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${
                    hotdealIsExpired
                      ? 'bg-slate-200 text-slate-600'
                      : 'bg-rose-100 text-rose-700'
                  }`}
                >
                  {hotdealIsExpired ? '마감됨' : '진행중'}
                </span>
                <span className="text-[12px] font-semibold text-rose-700">{hotdealDiscountRate}% 할인</span>
              </div>

              <p className="text-[15px] font-bold text-slate-900 leading-snug">
                {hotdealDetail?.productName ?? post.title}
              </p>

              <div className="mt-3 flex items-end gap-2">
                <strong className="text-[20px] font-bold text-slate-900">
                  {toWon(hotdealSummary?.dealPriceAmount ?? 0)}
                </strong>
                {(hotdealSummary?.originalPriceAmount ?? 0) > 0 && (
                  <span className="text-[13px] font-medium text-slate-400 line-through">
                    {toWon(hotdealSummary?.originalPriceAmount ?? 0)}
                  </span>
                )}
              </div>

              <div className="mt-3 grid grid-cols-1 gap-1.5 text-[12px] text-slate-600">
                <div>스토어: {hotdealDetail?.storeName || hotdealSummary?.storeName || '-'}</div>
                <div>배송: {hotdealDetail?.shippingInfo || '-'}</div>
                <div>
                  마감:{' '}
                  {hotdealSummary?.expiredAt ? formatDate(hotdealSummary.expiredAt) : '-'}
                </div>
              </div>

              {hotdealDetail?.dealUrl && (
                <div className="mt-3">
                  <a
                    href={hotdealDetail.dealUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[12px] font-bold text-rose-700 hover:bg-rose-100"
                  >
                    상품 링크 이동
                  </a>
                </div>
              )}
            </section>
          )}
        </div>

        <div className="mt-8 px-5 flex items-center gap-2">
          <button
            onClick={() => handleToggleReaction('LIKE')}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${
              selectedReaction === 'LIKE'
                ? 'border border-blue-500 bg-blue-50'
                : 'border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <svg
              className={`w-[18px] h-[18px] ${
                selectedReaction === 'LIKE' ? 'text-blue-600' : 'text-gray-800'
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
              />
            </svg>
            <span
              className={`text-[13px] font-medium ${
                selectedReaction === 'LIKE' ? 'text-blue-700' : 'text-gray-700'
              }`}
            >
              좋아요 {post.likeCount}
            </span>
          </button>

          <button
            onClick={() => handleToggleReaction('DISLIKE')}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 transition-colors ${
              selectedReaction === 'DISLIKE'
                ? 'border border-blue-500 bg-blue-50'
                : 'border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <svg
              className={`w-[18px] h-[18px] ${
                selectedReaction === 'DISLIKE' ? 'text-blue-600' : 'text-gray-800'
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
                selectedReaction === 'DISLIKE' ? 'text-blue-700' : 'text-gray-700'
              }`}
            >
              싫어요 {post.dislikeCount}
            </span>
          </button>
        </div>

        <div className="h-2.5 bg-gray-50 border-y border-gray-100 mt-6 w-full" />

        <div className="px-5 pt-6 pb-24 w-full">
          <h3 className="text-[15px] font-bold text-gray-900 mb-5">{post.commentCount}개의 댓글</h3>

          <div className="flex flex-col gap-6">
            {comments.length === 0 ? (
              <div className="text-center text-gray-400 text-[14px] py-6 font-medium">
                첫 번째 댓글을 남겨보세요.
              </div>
            ) : (
              comments.map((comment) => (
                <div key={comment.commentId} className="flex gap-3">
                  <div className="w-[34px] h-[34px] bg-gray-100 rounded-full overflow-hidden shrink-0 flex justify-center items-center font-bold text-gray-500 text-[14px]">
                    {(comment.authorNickname || '?')[0]}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-bold text-[14px] text-gray-900 truncate">
                          {comment.authorNickname || '알 수 없음'}
                        </span>
                        <span className="text-[12px] text-gray-400 font-medium tracking-tight">
                          {formatDate(comment.createdAt).split('.').slice(1, 4).join('.')}
                        </span>
                      </div>

                      {isCommentAuthor(comment) && (
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleEditComment(comment)}
                            className="text-[12px] font-medium text-gray-400 hover:text-gray-700"
                          >
                            수정
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteComment(comment.commentId)}
                            className="text-[12px] font-medium text-red-400 hover:text-red-600"
                          >
                            삭제
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="mt-1.5 text-[14px] text-gray-800 whitespace-pre-wrap leading-relaxed">
                      {comment.content}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {hasMoreComments && (
            <button
              type="button"
              onClick={loadMoreComments}
              className="w-full mt-6 py-3 rounded-xl border border-gray-200 text-[14px] font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              댓글 더 보기
            </button>
          )}
        </div>
      </div>

      <form
        onSubmit={handleCommentSubmit}
        className="sticky bottom-0 bg-white border-t border-gray-100 px-4 py-3"
      >
        <div className="flex items-center gap-2">
          <input
            value={commentInput}
            onChange={(e) => setCommentInput(e.target.value)}
            placeholder="댓글을 입력하세요."
            className="flex-1 h-11 px-4 rounded-full bg-gray-100 text-[14px] outline-none placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={submittingComment || !commentInput.trim()}
            className="h-11 px-4 rounded-full bg-blue-600 text-white text-[14px] font-bold disabled:bg-gray-300 transition-colors"
          >
            등록
          </button>
        </div>
      </form>
    </div>
  );
};
