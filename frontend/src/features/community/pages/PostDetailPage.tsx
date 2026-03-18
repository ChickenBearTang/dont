import axios from 'axios';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  createComment,
  deleteComment,
  deletePost,
  getComments,
  getPost,
  toggleReaction,
  updateComment,
} from '../api/communityApi';
import type { BoardCategory, CommentSummaryDto, GetPostResponseDto, ReactionType } from '../types';
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
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedReaction, setSelectedReaction] = useState<ReactionType | null>(null);

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
          setComments(commentsRes.data?.content || []);
          setHasMoreComments(commentsRes.data?.hasNext || false);
          setCommentPage(0);
          setSelectedReaction(null);
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
        setSelectedReaction(res.data.active ? res.data.reactionType : null);
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
            setSelectedReaction(cancelRes.data.active ? cancelRes.data.reactionType : null);
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

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!postId || !commentInput.trim()) return;

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
    <div className="bg-white min-h-[100dvh] flex flex-col pb-20 relative lg:max-w-2xl lg:mx-auto lg:border-x lg:border-gray-100 lg:shadow-sm">
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
                  onClick={() => alert('게시글 수정 페이지 연결 전입니다.')}
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
                            className="text-[12px] font-medium text-gray-500 hover:text-blue-600"
                            onClick={() => handleEditComment(comment)}
                          >
                            수정
                          </button>
                          <button
                            type="button"
                            className="text-[12px] font-medium text-gray-500 hover:text-red-500"
                            onClick={() => handleDeleteComment(comment.commentId)}
                          >
                            삭제
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="text-[14px] text-gray-800 leading-snug mt-1 w-full whitespace-pre-wrap word-break-all">
                      {comment.content}
                    </div>

                    <div className="mt-2 flex items-center gap-3">
                      <button className="inline-flex items-center gap-1 text-gray-500">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                          />
                        </svg>
                      </button>

                      <button className="inline-flex items-center gap-1 text-gray-500">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                          />
                        </svg>
                        <span className="text-[13px]">{comment.likeCount}</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}

            {hasMoreComments && (
              <div className="flex justify-center mt-2">
                <button
                  onClick={loadMoreComments}
                  className="px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-600 font-medium text-[13px] rounded-full transition-colors border border-gray-100"
                >
                  이전 댓글 더보기 ({(commentPage + 1) * 4} / {post.commentCount})
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="fixed bottom-0 lg:max-w-2xl lg:ml-[-1px] w-full bg-white border-t border-gray-100 flex items-center px-4 py-3 pb-8 lg:pb-3 z-20">
        <div className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center shrink-0 mr-3 text-gray-400 bg-gray-50">
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>

        <form
          onSubmit={handleCommentSubmit}
          className="flex-1 flex bg-gray-50 rounded-full items-center px-4 py-1 ring-1 ring-gray-100 focus-within:ring-gray-300 transition-shadow"
        >
          <input
            type="text"
            value={commentInput}
            onChange={(e) => setCommentInput(e.target.value)}
            placeholder="댓글을 작성해 보세요."
            className="flex-1 bg-transparent text-[14px] font-medium text-gray-800 placeholder:text-gray-400 outline-none w-full h-8"
            disabled={submittingComment}
          />
          <button
            type="submit"
            className={`font-bold text-[14px] ml-2 ${
              commentInput.trim() ? 'text-blue-500' : 'text-gray-300'
            }`}
            disabled={submittingComment || !commentInput.trim()}
          >
            등록
          </button>
        </form>
      </div>
    </div>
  );
};
